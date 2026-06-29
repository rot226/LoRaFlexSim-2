"""Agrégation automatique des résultats de campagnes de brouillage."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Iterable

GROUP_COLUMNS = ["scenario_name", "node_count", "adr_enabled", "channel_selection"]
COUNT_COLUMNS = ["seeds_count"]
REQUESTED_METRICS = [
    "pdr",
    "lost_packets",
    "loss_ratio",
    "energy_j",
    "energy_mj",
    "avg_energy_j",
    "mean_energy_j",
    "delay_s",
    "mean_delay_s",
    "avg_delay_s",
    "collided_packets",
    "collisions",
    "collision_ratio",
    "jammed_packets",
    "jammed_ratio",
    "channel_changes",
    "channel_change_count",
    "sf_changes",
    "sf_change_count",
]

COLUMN_ALIASES = {
    "scenario_name": ("scenario_name", "scenario", "name"),
    "node_count": ("node_count", "nodes", "N", "num_nodes"),
    "adr_enabled": ("adr_enabled", "adr", "ADR"),
    "channel_selection": ("channel_selection", "channel_policy", "channel_selection_policy"),
}


def aggregate_existing_results(input_dir: str | Path, output_path: str | Path) -> Path:
    """Agrège les ``run_summary.csv`` existants d'une campagne de brouillage.

    La recherche est récursive sous ``input_dir`` et accepte aussi un fichier CSV
    unique. Le CSV produit regroupe les runs par scénario, nombre de nœuds, ADR
    et politique de sélection de canal, puis calcule le nombre de seeds, les
    moyennes, écarts types et IC95 pour les métriques numériques disponibles.
    """

    root = Path(input_dir)
    summaries = _summary_files(root)
    rows = [row for path in summaries for row in _read_csv(path)]
    if not rows:
        raise FileNotFoundError(f"Aucun run_summary.csv trouvé sous {root}.")

    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = tuple(_normalize_group_value(row, column) for column in GROUP_COLUMNS)
        groups[key].append(row)

    metric_names = _metric_names(rows)
    fieldnames = GROUP_COLUMNS + COUNT_COLUMNS
    for metric in metric_names:
        fieldnames.extend([f"{metric}_mean", f"{metric}_std"])
        if metric == "pdr":
            fieldnames.extend(["pdr_ci95_low", "pdr_ci95_high", "pdr_ci95_half_width"])

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(groups):
            group_rows = groups[key]
            out: dict[str, Any] = dict(zip(GROUP_COLUMNS, key, strict=True))
            out["seeds_count"] = _seed_count(group_rows)
            for metric in metric_names:
                values = [_to_float(row.get(metric)) for row in group_rows]
                numeric = [value for value in values if value is not None and math.isfinite(value)]
                out[f"{metric}_mean"] = _fmt(mean(numeric)) if numeric else ""
                out[f"{metric}_std"] = _fmt(stdev(numeric)) if len(numeric) > 1 else _fmt(0.0) if numeric else ""
                if metric == "pdr":
                    half = _ci95_half_width(numeric)
                    avg = mean(numeric) if numeric else None
                    out["pdr_ci95_half_width"] = _fmt(half) if half is not None else ""
                    out["pdr_ci95_low"] = _fmt(max(0.0, avg - half)) if avg is not None and half is not None else ""
                    out["pdr_ci95_high"] = _fmt(min(1.0, avg + half)) if avg is not None and half is not None else ""
            writer.writerow(out)
    return output


def _summary_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("run_summary.csv") if path.is_file())


def _read_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def _normalize_group_value(row: dict[str, str], column: str) -> str:
    for name in COLUMN_ALIASES[column]:
        value = row.get(name)
        if value not in (None, ""):
            if column == "adr_enabled":
                return _normalize_bool(value)
            return str(value)
    return ""


def _normalize_bool(value: object) -> str:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return "true"
    if text in {"0", "false", "no", "off", "disabled"}:
        return "false"
    return str(value)


def _metric_names(rows: list[dict[str, str]]) -> list[str]:
    group_aliases = {alias for aliases in COLUMN_ALIASES.values() for alias in aliases}
    available = {key for row in rows for key in row if key not in group_aliases | {"seed"}}
    requested = [metric for metric in REQUESTED_METRICS if metric in available]
    numeric_extra = sorted(
        key for key in available - set(requested)
        if any(_to_float(row.get(key)) is not None for row in rows)
    )
    return requested + numeric_extra


def _seed_count(rows: list[dict[str, str]]) -> int:
    seeds = {str(row.get("seed", "")).strip() for row in rows if str(row.get("seed", "")).strip()}
    return len(seeds) if seeds else len(rows)


def _to_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ci95_half_width(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    return 1.96 * stdev(values) / math.sqrt(len(values))


def _fmt(value: float) -> str:
    return f"{value:.12g}"


__all__ = ["aggregate_existing_results"]

#!/usr/bin/env python3
"""Valide des critères minimaux de préparation IEEE sur des exports CSV.

Critères vérifiés:
1) diversité des séries par algorithme ;
2) absence de métriques anormalement constantes ;
3) tendance minimale attendue en SNIR_ON: N augmente => PDR ne doit pas augmenter ;
4) CDF monotone et non dégénérée.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ALGO_COLUMNS = ("algorithm", "algo")
N_COLUMNS = ("N", "num_nodes", "n_nodes")
PDR_COLUMNS = ("pdr", "pdr_mean")
SNIR_STATE_COLUMNS = ("snir_state", "snir", "mode", "snir_mode")
SNIR_FLAG_COLUMNS = ("with_snir", "use_snir", "snir_enabled")

DEFAULT_METRICS = ("pdr", "pdr_mean", "der", "der_mean", "throughput_bps", "throughput_bps_mean")


@dataclass(frozen=True)
class Failure:
    title: str
    details: str
    suggestion: str


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _pick_first_existing_column(rows: list[dict[str, str]], candidates: Iterable[str]) -> str | None:
    if not rows:
        return None
    keys = set(rows[0].keys())
    for candidate in candidates:
        if candidate in keys:
            return candidate
    return None


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y", "on", "snir_on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off", "snir_off"}:
        return False
    return None


def _parse_snir_state(row: dict[str, str]) -> str | None:
    for column in SNIR_STATE_COLUMNS:
        parsed = _parse_bool(row.get(column))
        if parsed is True:
            return "snir_on"
        if parsed is False:
            return "snir_off"
    for column in SNIR_FLAG_COLUMNS:
        parsed = _parse_bool(row.get(column))
        if parsed is True:
            return "snir_on"
        if parsed is False:
            return "snir_off"
    return None


def _get_algo(row: dict[str, str]) -> str:
    for column in ALGO_COLUMNS:
        value = (row.get(column) or "").strip()
        if value:
            return value
    return "<algo_inconnu>"


def _discover_csv_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in inputs:
        if path.is_file() and path.suffix.lower() == ".csv":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.csv")))
    return files


def _read_csv_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                row["__source"] = str(path)
                rows.append(row)
    return rows


def _check_series_diversity(rows: list[dict[str, str]], *, min_points: int, failures: list[Failure]) -> None:
    n_col = _pick_first_existing_column(rows, N_COLUMNS)
    if n_col is None:
        failures.append(
            Failure(
                title="Diversité des séries impossible",
                details="Aucune colonne de taille réseau détectée (N/num_nodes/n_nodes).",
                suggestion="Exporter une colonne N pour vérifier la diversité par algorithme.",
            )
        )
        return

    by_algo: dict[str, set[float]] = defaultdict(set)
    for row in rows:
        n_value = _to_float(row.get(n_col))
        if n_value is not None:
            by_algo[_get_algo(row)].add(n_value)

    for algo, points in sorted(by_algo.items()):
        if len(points) < min_points:
            rendered = ", ".join(f"{value:.6g}" for value in sorted(points)) if points else "aucun"
            failures.append(
                Failure(
                    title=f"Diversité insuffisante pour {algo}",
                    details=(
                        f"{len(points)} valeur(s) distincte(s) de {n_col} détectée(s) "
                        f"(minimum requis={min_points}). Valeurs: {rendered}."
                    ),
                    suggestion="Ajouter des points de simulation sur davantage de tailles de réseau.",
                )
            )


def _check_abnormal_constant_metrics(
    rows: list[dict[str, str]], *, metrics: list[str], tolerance: float, failures: list[Failure]
) -> None:
    available_metrics = [metric for metric in metrics if any(metric in row for row in rows)]
    if not available_metrics:
        failures.append(
            Failure(
                title="Contrôle de constance impossible",
                details="Aucune métrique demandée n'est présente dans les CSV.",
                suggestion="Vérifier les noms de colonnes via --metrics.",
            )
        )
        return

    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        algo = _get_algo(row)
        state = _parse_snir_state(row) or "snir_unknown"
        for metric in available_metrics:
            value = _to_float(row.get(metric))
            if value is not None:
                grouped[(algo, state, metric)].append(value)

    for (algo, state, metric), values in sorted(grouped.items()):
        if len(values) < 3:
            continue
        min_v = min(values)
        max_v = max(values)
        if abs(max_v - min_v) <= tolerance:
            failures.append(
                Failure(
                    title=f"Métrique constante suspecte ({metric})",
                    details=(
                        f"{algo}[{state}] présente {len(values)} points quasi identiques "
                        f"(min={min_v:.6g}, max={max_v:.6g}, tolérance={tolerance:g})."
                    ),
                    suggestion="Vérifier le pipeline d'agrégation et relancer avec des scénarios variés.",
                )
            )


def _check_min_expected_trend(rows: list[dict[str, str]], *, tolerance: float, failures: list[Failure]) -> None:
    n_col = _pick_first_existing_column(rows, N_COLUMNS)
    pdr_col = _pick_first_existing_column(rows, PDR_COLUMNS)
    if n_col is None or pdr_col is None:
        failures.append(
            Failure(
                title="Tendance N↑ -> PDR↓ impossible",
                details="Colonnes nécessaires absentes (N/num_nodes et pdr/pdr_mean).",
                suggestion="Inclure N et PDR dans les exports à valider.",
            )
        )
        return

    per_algo_n: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if _parse_snir_state(row) != "snir_on":
            continue
        n_value = _to_float(row.get(n_col))
        pdr_value = _to_float(row.get(pdr_col))
        if n_value is None or pdr_value is None:
            continue
        per_algo_n[_get_algo(row)][n_value].append(pdr_value)

    if not per_algo_n:
        failures.append(
            Failure(
                title="Aucune donnée SNIR_ON exploitable",
                details="Impossible de calculer la tendance N↑ -> PDR↓ sans lignes SNIR_ON valides.",
                suggestion="Exporter l'état SNIR et les colonnes N/PDR.",
            )
        )
        return

    for algo, by_n in sorted(per_algo_n.items()):
        if len(by_n) < 2:
            continue
        means = sorted((n, sum(values) / len(values)) for n, values in by_n.items())
        for (n_prev, pdr_prev), (n_next, pdr_next) in zip(means, means[1:]):
            if pdr_next > pdr_prev + tolerance:
                failures.append(
                    Failure(
                        title=f"Tendance invalide N↑ -> PDR↓ ({algo})",
                        details=(
                            f"En SNIR_ON, la PDR augmente entre N={n_prev:.6g} ({pdr_prev:.6g}) "
                            f"et N={n_next:.6g} ({pdr_next:.6g})."
                        ),
                        suggestion="Vérifier les données SNIR_ON (charge, collisions, appariement des scénarios).",
                    )
                )
                break


def _check_cdf_monotonic_and_non_degenerate(
    rows: list[dict[str, str]], *, tolerance: float, failures: list[Failure]
) -> None:
    cdf_rows = [row for row in rows if "cdf" in {k.lower() for k in row.keys()} or "quantile" in row]
    if not cdf_rows:
        failures.append(
            Failure(
                title="CDF non trouvée",
                details="Aucune colonne 'cdf' ou 'quantile' détectée dans les fichiers fournis.",
                suggestion="Inclure un export CDF (ex: quantile/sinr_db ou value/cdf).",
            )
        )
        return

    # Détection des colonnes CDF usuelles.
    cdf_col = None
    for candidate in ("cdf", "ecdf", "probability", "quantile"):
        cdf_col = _pick_first_existing_column(cdf_rows, [candidate])
        if cdf_col:
            break

    x_col = None
    for candidate in ("sinr_db", "snr_db", "rssi_dbm", "value", "x"):
        x_col = _pick_first_existing_column(cdf_rows, [candidate])
        if x_col:
            break

    if cdf_col is None or x_col is None:
        failures.append(
            Failure(
                title="Colonnes CDF incomplètes",
                details=f"Colonnes détectées: cdf={cdf_col!r}, axe={x_col!r}.",
                suggestion="Fournir au minimum une paire (x, cdf) exploitable.",
            )
        )
        return

    groups: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for row in cdf_rows:
        x_val = _to_float(row.get(x_col))
        cdf_val = _to_float(row.get(cdf_col))
        if x_val is None or cdf_val is None:
            continue
        groups[(_get_algo(row), _parse_snir_state(row) or "snir_unknown")].append((x_val, cdf_val))

    for key, pairs in sorted(groups.items()):
        if len(pairs) < 2:
            continue
        pairs.sort(key=lambda item: item[0])
        xs = [item[0] for item in pairs]
        ys = [item[1] for item in pairs]

        if max(xs) - min(xs) <= tolerance:
            failures.append(
                Failure(
                    title=f"CDF dégénérée ({key[0]}[{key[1]}])",
                    details=(
                        f"Toutes les abscisses sont identiques (x={xs[0]:.6g}, tolérance={tolerance:g})."
                    ),
                    suggestion="Vérifier l'échantillonnage et l'export des valeurs source de la CDF.",
                )
            )
            continue

        if max(ys) - min(ys) <= tolerance:
            failures.append(
                Failure(
                    title=f"CDF plate ({key[0]}[{key[1]}])",
                    details=(
                        f"Toutes les ordonnées CDF sont identiques (y≈{ys[0]:.6g}, tolérance={tolerance:g})."
                    ),
                    suggestion="Recalculer la CDF: elle doit progresser de 0 vers 1.",
                )
            )
            continue

        for prev, curr in zip(ys, ys[1:]):
            if curr + tolerance < prev:
                failures.append(
                    Failure(
                        title=f"CDF non monotone ({key[0]}[{key[1]}])",
                        details=f"La CDF décroît localement ({prev:.6g} -> {curr:.6g}).",
                        suggestion="Trier les points par x avant export et corriger le calcul cumulé.",
                    )
                )
                break


def validate(args: argparse.Namespace) -> list[Failure]:
    csv_files = _discover_csv_files(args.inputs)
    if not csv_files:
        return [
            Failure(
                title="Aucun CSV détecté",
                details="Aucun fichier .csv trouvé dans les chemins fournis.",
                suggestion="Passer un fichier CSV ou un répertoire contenant les exports.",
            )
        ]

    rows = _read_csv_rows(csv_files)
    if not rows:
        return [
            Failure(
                title="CSV vides",
                details="Les fichiers trouvés ne contiennent aucune ligne exploitable.",
                suggestion="Vérifier l'export des simulations.",
            )
        ]

    failures: list[Failure] = []
    _check_series_diversity(rows, min_points=args.min_points, failures=failures)
    _check_abnormal_constant_metrics(rows, metrics=args.metrics, tolerance=args.tolerance, failures=failures)
    _check_min_expected_trend(rows, tolerance=args.tolerance, failures=failures)
    _check_cdf_monotonic_and_non_degenerate(rows, tolerance=args.tolerance, failures=failures)
    return failures


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+", help="Fichier(s) CSV ou dossier(s) à valider.")
    parser.add_argument(
        "--min-points",
        type=int,
        default=3,
        help="Nombre minimal de valeurs distinctes de N par algorithme.",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=list(DEFAULT_METRICS),
        help="Colonnes métriques à contrôler pour détecter des séries constantes.",
    )
    parser.add_argument("--tolerance", type=float, default=1e-9, help="Tolérance numérique.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    failures = validate(args)
    if failures:
        print("❌ Validation IEEE échouée.")
        for idx, failure in enumerate(failures, start=1):
            print(f"\n[{idx}] {failure.title}")
            print(f"    Diagnostic : {failure.details}")
            print(f"    Suggestion : {failure.suggestion}")
        return 1

    print("✅ Validation IEEE réussie: critères de readiness satisfaits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

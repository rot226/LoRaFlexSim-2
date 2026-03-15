"""Validateur QA strict pour les sorties d'agrégation/plots mobilesfrdth."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

METRICS = (
    "pdr_mean",
    "der_mean",
    "throughput_bps_mean",
    "jain_fairness_mean",
    "airtime_total_s_mean",
    "switch_count_mean",
)

ATOL_EQUAL = 1e-6
RTOL_EQUAL = 1e-3
VARIANCE_EPS = 1e-8


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    token = value.strip()
    if not token:
        return None
    try:
        parsed = float(token)
    except ValueError:
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed



def _check_algorithms_quasi_identiques(rows: list[dict[str, str]]) -> str | None:
    if not rows:
        return None

    all_columns = set(rows[0])
    context_cols = tuple(sorted(column for column in all_columns if column not in set(METRICS) | {"algo"}))
    by_context: dict[tuple[str, ...], dict[str, dict[str, float]]] = defaultdict(dict)

    for row in rows:
        algo = str(row.get("algo", "")).strip().lower()
        if not algo:
            continue
        context = tuple(str(row.get(col, "")).strip() for col in context_cols)
        metric_values: dict[str, float] = {}
        for metric in METRICS:
            value = _to_float(row.get(metric))
            if value is not None:
                metric_values[metric] = value
        if metric_values:
            by_context[context][algo] = metric_values

    if not by_context:
        return None

    metric_uniform: dict[str, list[bool]] = defaultdict(list)
    for algos in by_context.values():
        if len(algos) < 2:
            continue
        for metric in METRICS:
            values = [algo_metrics[metric] for algo_metrics in algos.values() if metric in algo_metrics]
            if len(values) < 2:
                continue
            spread = max(values) - min(values)
            threshold = ATOL_EQUAL + RTOL_EQUAL * max(max(abs(v) for v in values), 1.0)
            metric_uniform[metric].append(spread <= threshold)

    if not metric_uniform:
        return None

    all_uniform = all(flags and all(flags) for flags in metric_uniform.values() if flags)
    if all_uniform and len([metric for metric, flags in metric_uniform.items() if flags]) == len(METRICS):
        return "Toutes les algorithmes semblent quasi identiques sur toutes les métriques (écarts sous seuil)."
    return None


def _check_variance_quasi_nulle(rows: list[dict[str, str]]) -> str | None:
    if not rows:
        return None
    per_metric: dict[str, list[float]] = {metric: [] for metric in METRICS}
    for row in rows:
        for metric in METRICS:
            value = _to_float(row.get(metric))
            if value is not None:
                per_metric[metric].append(value)

    available = {metric: values for metric, values in per_metric.items() if len(values) >= 2}
    if not available:
        return None

    if all(statistics.pvariance(values) <= VARIANCE_EPS for values in available.values()):
        return "Variance quasi nulle sur toutes les métriques de metric_by_factor.csv."
    return None


def _check_tc_constant(rows: list[dict[str, str]]) -> str | None:
    values = [_to_float(row.get("Tc_s")) for row in rows]
    values = [value for value in values if value is not None]
    if len(values) < 2:
        return None
    if max(values) - min(values) <= ATOL_EQUAL:
        return "Tc_s est constant pour tous les cas de convergence_tc.csv."
    return None


def _check_cdf_monotonic(rows: list[dict[str, str]]) -> list[str]:
    issues: list[str] = []
    if not rows:
        return issues

    context_cols = ("algo", "mode", "N", "speed", "mobility_model", "gateways", "sigma")
    by_group: dict[tuple[str, ...], list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        quantile = _to_float(row.get("quantile"))
        sinr = _to_float(row.get("sinr_db"))
        if quantile is None or sinr is None:
            continue
        key = tuple(str(row.get(col, "")) for col in context_cols)
        by_group[key].append((quantile, sinr))

    for key, points in by_group.items():
        points.sort(key=lambda point: (point[0], point[1]))
        quantiles = [point[0] for point in points]
        sinrs = [point[1] for point in points]
        label = ", ".join(f"{name}={value}" for name, value in zip(context_cols, key, strict=False))

        if any(q <= 0.0 or q > 1.0 for q in quantiles):
            issues.append(f"CDF invalide ({label}): quantile hors ]0,1].")
            continue
        if any(curr < prev for prev, curr in zip(quantiles, quantiles[1:], strict=False)):
            issues.append(f"CDF non monotone ({label}): quantile décroissant.")
            continue
        if any(curr < prev for prev, curr in zip(sinrs, sinrs[1:], strict=False)):
            issues.append(f"CDF non monotone ({label}): sinr_db décroissant.")

    return issues


def _check_figure_traces(figure_filters: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for trace in figure_filters:
        figure = str(trace.get("figure", "<unknown>"))
        generated = bool(trace.get("generated", False))
        num_points = int(trace.get("num_points", 0) or 0)
        if not generated:
            issues.append(f"Figure non générée: {figure}.")
            continue
        if num_points <= 0:
            issues.append(f"Figure vide/sans points: {figure}.")
    return issues


def validate_strict_plot_outputs(*, aggregates_dir: Path, figure_filters: list[dict[str, Any]]) -> list[str]:
    """Retourne la liste des anomalies bloquantes détectées en mode strict."""

    issues: list[str] = []
    metric_rows = _read_csv(aggregates_dir / "metric_by_factor.csv")
    tc_rows = _read_csv(aggregates_dir / "convergence_tc.csv")
    cdf_rows = _read_csv(aggregates_dir / "sinr_cdf.csv")

    quasi_identiques = _check_algorithms_quasi_identiques(metric_rows)
    if quasi_identiques:
        issues.append(quasi_identiques)

    variance_nulle = _check_variance_quasi_nulle(metric_rows)
    if variance_nulle:
        issues.append(variance_nulle)

    tc_constant = _check_tc_constant(tc_rows)
    if tc_constant:
        issues.append(tc_constant)

    issues.extend(_check_cdf_monotonic(cdf_rows))
    issues.extend(_check_figure_traces(figure_filters))
    return issues


def _existing_path(value: str) -> Path:
    path = Path(value)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"Chemin introuvable: {path}")
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Valide strictement les sorties d'agrégats/figures mobilesfrdth.")
    parser.add_argument("--aggregates-dir", type=_existing_path, required=True)
    parser.add_argument("--plots-summary", type=_existing_path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    import json

    report = json.loads(args.plots_summary.read_text(encoding="utf-8"))
    figure_filters = report.get("figure_filters", [])
    issues = validate_strict_plot_outputs(
        aggregates_dir=args.aggregates_dir,
        figure_filters=figure_filters,
    )
    if issues:
        print("Validation stricte: ÉCHEC")
        for issue in issues:
            print(f"- {issue}")
        return 2

    print("Validation stricte: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

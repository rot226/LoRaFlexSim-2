#!/usr/bin/env python3
"""Valide des invariants métier sur les CSV d'agrégats d'article.

Le script contrôle notamment :
- la non-constance de PDR/DER/throughput selon N ;
- la présence de plusieurs quantiles dans la CDF SINR ;
- la présence d'au moins un algo avec switch_count et airtime_total_s non nuls ;
- un écart mesurable SNIR_ON vs SNIR_OFF sur au moins une métrique.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _to_float(value: str | None, *, default: float = math.nan) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _assert_metric_not_constant_over_n(
    rows: list[dict[str, str]],
    *,
    metric_col: str,
    metric_label: str,
    failures: list[str],
    tolerance: float,
) -> None:
    by_n: dict[int, list[float]] = defaultdict(list)
    invalid_n_rows = 0
    invalid_metric_rows = 0
    for row in rows:
        n_value = _to_float(row.get("N"))
        metric_value = _to_float(row.get(metric_col))
        if math.isnan(n_value):
            invalid_n_rows += 1
            continue
        if math.isnan(metric_value):
            invalid_metric_rows += 1
            continue
        by_n[int(round(n_value))].append(metric_value)

    if len(by_n) < 2:
        failures.append(
            f"{metric_label}: impossible de vérifier la variation sur N (moins de 2 valeurs distinctes de N)."
        )
        return

    means = {n: (sum(values) / len(values)) for n, values in by_n.items() if values}
    ordered = sorted(means.items())
    baseline = ordered[0][1]
    if all(abs(value - baseline) <= tolerance for _, value in ordered[1:]):
        values_repr = ", ".join(f"N={n}: {value:.6g}" for n, value in ordered)
        failures.append(
            f"{metric_label}: constante sur tous les N (tolérance={tolerance:g}). Valeurs: {values_repr}."
        )

    if invalid_n_rows:
        failures.append(
            f"{metric_label}: {invalid_n_rows} ligne(s) ignorée(s) car N est invalide."
        )
    if invalid_metric_rows:
        failures.append(
            f"{metric_label}: {invalid_metric_rows} ligne(s) ignorée(s) car {metric_col} est invalide."
        )


def _check_sinr_cdf(rows: list[dict[str, str]], failures: list[str], tolerance: float) -> None:
    quantiles = sorted({_to_float(row.get("quantile")) for row in rows if not math.isnan(_to_float(row.get("quantile")))})
    if len(quantiles) < 2:
        failures.append("SINR CDF: moins de 2 quantiles distincts dans sinr_cdf.csv.")
        return

    sinr_values = [_to_float(row.get("sinr_db")) for row in rows]
    sinr_values = [value for value in sinr_values if not math.isnan(value)]
    if len(sinr_values) < 2:
        failures.append("SINR CDF: moins de 2 valeurs SINR exploitables dans sinr_cdf.csv.")
        return

    baseline = sinr_values[0]
    if all(abs(value - baseline) <= tolerance for value in sinr_values[1:]):
        failures.append(
            f"SINR CDF: toutes les valeurs sinr_db sont identiques (tolérance={tolerance:g})."
        )


def _check_airtime_and_switch_non_zero(rows: list[dict[str, str]], failures: list[str], tolerance: float) -> None:
    if not rows:
        failures.append("fairness_airtime_switching.csv est vide : impossible de valider airtime/switch_count.")
        return

    by_algo: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        algo = (row.get("algo") or "").strip() or "<algo_vide>"
        airtime = _to_float(row.get("airtime_total_s"), default=0.0)
        switch_count = _to_float(row.get("switch_count"), default=0.0)
        by_algo[algo].append((airtime, switch_count))

    algo_ok = []
    for algo, values in by_algo.items():
        has_non_zero = any((abs(airtime) > tolerance and abs(switch) > tolerance) for airtime, switch in values)
        if has_non_zero:
            algo_ok.append(algo)

    if not algo_ok:
        failures.append(
            "Aucun algo ne présente simultanément airtime_total_s et switch_count non nuls dans fairness_airtime_switching.csv."
        )


def _check_snir_on_vs_off_metric_gap(rows: list[dict[str, str]], failures: list[str], tolerance: float) -> None:
    if not rows:
        failures.append("metric_by_factor.csv est vide : impossible de comparer SNIR_ON vs SNIR_OFF.")
        return

    metrics = [
        "pdr_mean",
        "der_mean",
        "throughput_bps_mean",
        "airtime_total_s_mean",
        "switch_count_mean",
    ]
    available_metrics = [metric for metric in metrics if any(metric in row for row in rows)]
    if not available_metrics:
        failures.append("Aucune métrique exploitable trouvée pour comparer SNIR_ON vs SNIR_OFF.")
        return

    groups: dict[tuple[str, str, str, str, str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        mode = (row.get("mode") or "").strip().lower()
        if mode not in {"snir_on", "snir_off"}:
            continue
        key = (
            (row.get("N") or "").strip(),
            (row.get("algo") or "").strip(),
            (row.get("speed") or "").strip(),
            (row.get("mobility_model") or "").strip(),
            (row.get("gateways") or "").strip(),
            (row.get("sigma") or "").strip(),
        )
        groups[key][mode] = row

    measurable_diffs: list[str] = []
    matched_groups = 0
    for key, mode_rows in groups.items():
        if "snir_on" not in mode_rows or "snir_off" not in mode_rows:
            continue
        matched_groups += 1
        row_on = mode_rows["snir_on"]
        row_off = mode_rows["snir_off"]
        for metric in available_metrics:
            on_value = _to_float(row_on.get(metric))
            off_value = _to_float(row_off.get(metric))
            if math.isnan(on_value) or math.isnan(off_value):
                continue
            delta = abs(on_value - off_value)
            if delta > tolerance:
                measurable_diffs.append(
                    f"groupe={key}, métrique={metric}, on={on_value:.6g}, off={off_value:.6g}, Δ={delta:.6g}"
                )

    if matched_groups == 0:
        failures.append("Aucun groupe apparié SNIR_ON/SNIR_OFF trouvé dans metric_by_factor.csv.")
        return

    if not measurable_diffs:
        failures.append(
            "Différence SNIR_ON vs SNIR_OFF non mesurable: toutes les métriques appariées sont égales dans la tolérance."
        )


def validate(aggregates_dir: Path, *, tolerance: float) -> list[str]:
    failures: list[str] = []

    metric_path = aggregates_dir / "metric_by_factor.csv"
    sinr_path = aggregates_dir / "sinr_cdf.csv"
    fairness_path = aggregates_dir / "fairness_airtime_switching.csv"

    for required in (metric_path, sinr_path, fairness_path):
        if not required.is_file():
            failures.append(f"Fichier requis manquant: {required}")

    if failures:
        return failures

    metric_rows = _read_csv(metric_path)
    sinr_rows = _read_csv(sinr_path)
    fairness_rows = _read_csv(fairness_path)

    if not metric_rows:
        failures.append(f"{metric_path} est vide.")
    if not sinr_rows:
        failures.append(f"{sinr_path} est vide.")
    if not fairness_rows:
        failures.append(f"{fairness_path} est vide.")
    if failures:
        return failures

    _assert_metric_not_constant_over_n(
        metric_rows,
        metric_col="pdr_mean",
        metric_label="PDR",
        failures=failures,
        tolerance=tolerance,
    )
    _assert_metric_not_constant_over_n(
        metric_rows,
        metric_col="der_mean",
        metric_label="DER",
        failures=failures,
        tolerance=tolerance,
    )
    _assert_metric_not_constant_over_n(
        metric_rows,
        metric_col="throughput_bps_mean",
        metric_label="throughput",
        failures=failures,
        tolerance=tolerance,
    )

    _check_sinr_cdf(sinr_rows, failures, tolerance)
    _check_airtime_and_switch_non_zero(fairness_rows, failures, tolerance)
    _check_snir_on_vs_off_metric_gap(metric_rows, failures, tolerance)

    return failures


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valide les métriques agrégées d'article.")
    parser.add_argument(
        "--aggregates-dir",
        type=Path,
        default=Path("aggregates"),
        help="Répertoire contenant metric_by_factor.csv, sinr_cdf.csv et fairness_airtime_switching.csv.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-6,
        help="Tolérance numérique pour les comparaisons d'égalité.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    failures = validate(args.aggregates_dir, tolerance=args.tolerance)
    if failures:
        print("Validation échouée :")
        for issue in failures:
            print(f" - {issue}")
        return 1

    print("Validation réussie : tous les invariants sont satisfaits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Valide la cohérence des sorties article (agrégats + CDF SINR + fairness).

Vérifications effectuées :
1) absence de séries PDR/DER identiques entre tous les algorithmes ;
2) PDR et DER non constants ;
3) monotonie de la CDF SINR (quantile croissant => SINR non décroissant) ;
4) plausibilité de switch_count (fini, >= 0, quasi-entier, borné).
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


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _check_not_constant(rows: list[dict[str, str]], metric: str, failures: list[str], tolerance: float) -> None:
    by_n: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        n = _to_float(row.get("N"))
        m = _to_float(row.get(metric))
        if math.isnan(n) or math.isnan(m):
            continue
        by_n[int(round(n))].append(m)

    if len(by_n) < 2:
        failures.append(
            f"{metric}: impossible de vérifier la non-constance (moins de 2 valeurs distinctes de N)."
        )
        return

    ordered = sorted((n, _mean(values)) for n, values in by_n.items() if values)
    baseline = ordered[0][1]
    if all(abs(v - baseline) <= tolerance for _, v in ordered[1:]):
        rendered = ", ".join(f"N={n}:{v:.6g}" for n, v in ordered)
        failures.append(f"{metric}: série constante sur N. Valeurs={rendered}.")


def _build_algo_series_signature(
    rows: list[dict[str, str]], metric: str, tolerance: float
) -> dict[str, tuple[tuple[int, float], ...]]:
    by_algo_n: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        algo = (row.get("algo") or "").strip()
        n = _to_float(row.get("N"))
        val = _to_float(row.get(metric))
        if not algo or math.isnan(n) or math.isnan(val):
            continue
        by_algo_n[algo][int(round(n))].append(val)

    signatures: dict[str, tuple[tuple[int, float], ...]] = {}
    for algo, series in by_algo_n.items():
        ordered = sorted((n, _mean(values)) for n, values in series.items() if values)
        rounded = tuple((n, round(v / tolerance) * tolerance) for n, v in ordered)
        signatures[algo] = rounded
    return signatures


def _check_no_identical_series_between_algos(
    rows: list[dict[str, str]], failures: list[str], tolerance: float
) -> None:
    for metric in ("pdr_mean", "der_mean"):
        signatures = _build_algo_series_signature(rows, metric, tolerance)
        if len(signatures) < 2:
            failures.append(
                f"{metric}: impossible de comparer les algorithmes (moins de 2 algorithmes exploitables)."
            )
            continue

        unique_signatures = {sig for sig in signatures.values()}
        if len(unique_signatures) == 1:
            algos = ", ".join(sorted(signatures))
            failures.append(
                f"{metric}: séries identiques pour tous les algorithmes ({algos})."
            )


def _check_sinr_cdf_monotone(rows: list[dict[str, str]], failures: list[str], tolerance: float) -> None:
    group_columns = [
        c for c in rows[0].keys() if c not in {"quantile", "sinr_db", "cdf", "probability"}
    ]
    grouped: dict[tuple[str, ...], list[tuple[float, float]]] = defaultdict(list)

    for row in rows:
        q = _to_float(row.get("quantile"))
        s = _to_float(row.get("sinr_db"))
        if math.isnan(q) or math.isnan(s):
            continue
        key = tuple((row.get(col) or "").strip() for col in group_columns)
        grouped[key].append((q, s))

    if not grouped:
        failures.append("SINR CDF: aucune paire (quantile, sinr_db) exploitable.")
        return

    for key, values in grouped.items():
        values.sort(key=lambda item: item[0])
        for i in range(1, len(values)):
            q_prev, s_prev = values[i - 1]
            q_cur, s_cur = values[i]
            if q_cur + tolerance < q_prev:
                failures.append(f"SINR CDF: quantiles non triés pour groupe {key}.")
                break
            if s_cur + tolerance < s_prev:
                failures.append(
                    "SINR CDF non monotone: "
                    f"groupe={key}, quantile {q_prev:.4g}->{q_cur:.4g}, "
                    f"sinr_db {s_prev:.6g}->{s_cur:.6g}."
                )
                break


def _check_switch_count_plausible(rows: list[dict[str, str]], failures: list[str], tolerance: float) -> None:
    values: list[float] = []
    for idx, row in enumerate(rows, start=2):
        val = _to_float(row.get("switch_count"))
        if math.isnan(val):
            failures.append(f"switch_count invalide à la ligne {idx} de fairness_airtime_switching.csv.")
            continue
        values.append(val)
        if not math.isfinite(val):
            failures.append(f"switch_count non fini à la ligne {idx}: {val}.")
            continue
        if val < -tolerance:
            failures.append(f"switch_count négatif à la ligne {idx}: {val}.")
        if abs(val - round(val)) > tolerance:
            failures.append(f"switch_count non entier à la ligne {idx}: {val}.")
        if val > 1_000_000:
            failures.append(f"switch_count implausible (> 1e6) à la ligne {idx}: {val}.")

    if not values:
        failures.append("switch_count: aucune valeur exploitable.")


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

    _check_no_identical_series_between_algos(metric_rows, failures, tolerance)
    _check_not_constant(metric_rows, "pdr_mean", failures, tolerance)
    _check_not_constant(metric_rows, "der_mean", failures, tolerance)
    _check_sinr_cdf_monotone(sinr_rows, failures, tolerance)
    _check_switch_count_plausible(fairness_rows, failures, tolerance)

    return failures


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vérifie la cohérence des métriques article.")
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
        help="Tolérance numérique utilisée pour les comparaisons.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    failures = validate(args.aggregates_dir, tolerance=args.tolerance)
    if failures:
        print("Validation échouée :")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("Validation réussie : cohérence article vérifiée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

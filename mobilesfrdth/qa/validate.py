"""Validation QA des agrégats CSV pour la commande ``mobilesfrdth validate``."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

GROUP_COLUMNS = ("N", "speed", "mobility_model", "mode", "algo", "gateways", "sigma_shadowing")
METRIC_COLUMNS = ("pdr_mean", "der_mean", "throughput_bps_mean", "Tc_s_mean", "jain_fairness_mean")


@dataclass(slots=True)
class ValidationReport:
    """Résultat d'une validation QA."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def has_issues(self) -> bool:
        return bool(self.errors or self.warnings)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    token = value.strip()
    if token == "":
        return None
    try:
        parsed = float(token)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _check_required_columns(*, file_label: str, actual: list[str], required: tuple[str, ...], report: ValidationReport) -> None:
    missing = [column for column in required if column not in actual]
    if missing:
        report.errors.append(f"{file_label}: colonnes manquantes: {', '.join(missing)}")


def _check_numeric_columns(*, file_label: str, rows: list[dict[str, str]], columns: tuple[str, ...], report: ValidationReport) -> None:
    for row_idx, row in enumerate(rows, start=2):
        for column in columns:
            raw = row.get(column)
            if _parse_float(raw) is None:
                report.errors.append(f"{file_label}: valeur non numérique/NaN/inf pour '{column}' ligne {row_idx} ({raw!r})")


def _check_group_cardinality(rows: list[dict[str, str]], report: ValidationReport) -> None:
    groups: set[tuple[str, ...]] = set()
    by_context: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for row in rows:
        key = tuple(str(row.get(column, "")).strip() for column in GROUP_COLUMNS)
        if key in groups:
            report.errors.append("metric_by_factor.csv: groupe dupliqué détecté (cardinalité invalide).")
            break
        groups.add(key)
        context_key = key[:-4] + key[-2:]
        by_context[context_key].add(key[4])

    for context_key, algos in by_context.items():
        if len(algos) < 2:
            context = ", ".join(context_key)
            report.warnings.append(
                "metric_by_factor.csv: contexte avec moins de 2 algorithmes "
                f"(comparaison faible): {context}"
            )


def _check_statistical_consistency(rows: list[dict[str, str]], report: ValidationReport) -> None:
    if not rows:
        report.errors.append("metric_by_factor.csv: fichier vide.")
        return

    metric_values: dict[str, list[float]] = {metric: [] for metric in METRIC_COLUMNS}
    for row in rows:
        runs = _parse_float(row.get("n_runs_effective"))
        if runs is None or runs < 2:
            report.errors.append("metric_by_factor.csv: n_runs_effective insuffisant (<2) pour calculer des IC fiables.")
        for metric in METRIC_COLUMNS:
            value = _parse_float(row.get(metric))
            if value is not None:
                metric_values[metric].append(value)
        for metric_name in ("pdr", "der", "throughput_bps", "Tc_s", "jain_fairness"):
            n_col = f"{metric_name}_n"
            ci_col = f"{metric_name}_ci95"
            if n_col in row and ci_col in row:
                n_value = _parse_float(row.get(n_col))
                ci_value = _parse_float(row.get(ci_col))
                if n_value is None or n_value < 2:
                    report.errors.append(f"metric_by_factor.csv: {n_col} insuffisant (<2).")
                if ci_value is None:
                    report.errors.append(f"metric_by_factor.csv: {ci_col} non calculable.")

    for metric, values in metric_values.items():
        if len(values) >= 2 and (max(values) - min(values)) <= 1e-12:
            report.warnings.append(f"metric_by_factor.csv: courbe potentiellement dégénérée, {metric} constant.")


def _check_cdf(rows: list[dict[str, str]], report: ValidationReport) -> None:
    by_group: dict[tuple[str, ...], list[tuple[float, float]]] = defaultdict(list)
    group_columns = GROUP_COLUMNS
    for row_idx, row in enumerate(rows, start=2):
        quantile = _parse_float(row.get("quantile"))
        sinr = _parse_float(row.get("sinr_db"))
        if quantile is None or sinr is None:
            report.errors.append(f"sinr_cdf.csv: ligne {row_idx} avec quantile/sinr_db invalide (NaN/inf/type).")
            continue
        if quantile <= 0.0 or quantile > 1.0:
            report.errors.append(f"sinr_cdf.csv: quantile hors ]0,1] ligne {row_idx} ({quantile}).")
            continue
        key = tuple(str(row.get(column, "")).strip() for column in group_columns)
        by_group[key].append((quantile, sinr))

    for key, points in by_group.items():
        points.sort(key=lambda point: point[0])
        for (q_prev, s_prev), (q_curr, s_curr) in zip(points, points[1:], strict=False):
            if q_curr < q_prev:
                report.errors.append(f"sinr_cdf.csv: CDF non monotone (quantile décroissant) pour groupe={key}.")
                break
            if s_curr < s_prev:
                report.errors.append(f"sinr_cdf.csv: CDF non monotone (sinr_db décroissant) pour groupe={key}.")
                break


def validate_aggregates(aggregates_dir: Path) -> ValidationReport:
    """Exécute les vérifications QA minimales sur un dossier ``aggregates``."""

    report = ValidationReport()
    metric_headers, metric_rows = _read_csv(aggregates_dir / "metric_by_factor.csv")
    cdf_headers, cdf_rows = _read_csv(aggregates_dir / "sinr_cdf.csv")
    conv_headers, conv_rows = _read_csv(aggregates_dir / "convergence_tc.csv")

    if not metric_headers:
        report.errors.append("Fichier manquant ou vide: metric_by_factor.csv")
        return report

    _check_required_columns(
        file_label="metric_by_factor.csv",
        actual=metric_headers,
        required=GROUP_COLUMNS + ("n_runs_effective",) + METRIC_COLUMNS,
        report=report,
    )
    _check_numeric_columns(
        file_label="metric_by_factor.csv",
        rows=metric_rows,
        columns=("n_runs_effective",) + METRIC_COLUMNS,
        report=report,
    )
    _check_group_cardinality(metric_rows, report)
    _check_statistical_consistency(metric_rows, report)

    if not conv_headers:
        report.errors.append("Fichier manquant ou vide: convergence_tc.csv")
    else:
        _check_required_columns(
            file_label="convergence_tc.csv",
            actual=conv_headers,
            required=GROUP_COLUMNS + ("run_id", "Tc_s"),
            report=report,
        )
        _check_numeric_columns(file_label="convergence_tc.csv", rows=conv_rows, columns=("Tc_s",), report=report)

    if not cdf_headers:
        report.errors.append("Fichier manquant ou vide: sinr_cdf.csv")
    else:
        _check_required_columns(
            file_label="sinr_cdf.csv",
            actual=cdf_headers,
            required=GROUP_COLUMNS + ("quantile", "sinr_db"),
            report=report,
        )
        _check_cdf(cdf_rows, report)

    return report


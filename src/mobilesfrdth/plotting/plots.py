"""Génération des figures à partir de ``aggregates/*.csv`` uniquement."""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .utils import ci95_from_samples, normalized_axis_label, setup_plot_style, PLOT_DPI



REQUIRED_FILES = {
    "metric_by_factor": "metric_by_factor.csv",
    "distribution_sf": "distribution_sf.csv",
    "convergence_tc": "convergence_tc.csv",
    "sinr_cdf": "sinr_cdf.csv",
    "fairness_airtime_switching": "fairness_airtime_switching.csv",
    "ucb_tracking": "ucb_tracking.csv",
}

REQUIRED_COLUMNS = {
    "metric_by_factor": {
        "N",
        "algo",
        "mode",
        "pdr_mean",
        "der_mean",
        "throughput_bps_mean",
        "jain_fairness_mean",
        "airtime_total_s_mean",
        "switch_count_mean",
    },
    "distribution_sf": {"algo", "sf", "ratio"},
    "convergence_tc": {"algo", "speed", "Tc_s"},
    "sinr_cdf": {"algo", "mode", "N", "speed", "quantile", "sinr_db"},
    "fairness_airtime_switching": {"N", "algo", "jain_fairness", "airtime_total_s", "switch_count"},
    "ucb_tracking": {"speed", "mode", "algo", "Tc_s_mean"},
}

FIGURE_SPECS = [
    ("fig01_pdr_vs_n_snir_off.png", "metric_by_factor", "pdr_mean", {"mode": {"snir_off"}}),
    ("fig02_pdr_vs_n_snir_on.png", "metric_by_factor", "pdr_mean", {"mode": {"snir_on"}}),
    ("fig03_der_vs_n_snir_off.png", "metric_by_factor", "der_mean", {"mode": {"snir_off"}}),
    ("fig04_der_vs_n_snir_on.png", "metric_by_factor", "der_mean", {"mode": {"snir_on"}}),
    ("fig05_throughput_vs_n_snir_off.png", "metric_by_factor", "throughput_bps_mean", {"mode": {"snir_off"}}),
    ("fig06_throughput_vs_n_snir_on.png", "metric_by_factor", "throughput_bps_mean", {"mode": {"snir_on"}}),
]

BONUS_SPECS = [
    ("fig11_airtime_vs_n.png", "metric_by_factor", "airtime_total_s_mean", {}),
    ("fig12_switch_count_vs_n.png", "metric_by_factor", "switch_count_mean", {}),
    ("fig13_ucb_tracking_lag_vs_speed.png", "ucb_tracking", "Tc_s_mean", {"algo": {"ucb", "ucb_forget"}}),
    ("fig14_reliability_airtime_pareto.png", "metric_by_factor", "pdr_mean", {}),
    ("fig15_outage_tail_prob_vs_n.png", "sinr_cdf", "sinr_db", {}),
    ("fig16_fairness_reliability_tradeoff.png", "metric_by_factor", "pdr_mean", {}),
]

ARTICLE_PROFILE_FILTERS: dict[str, dict[str, dict[str, set[str]]]] = {
    "core": {
        "fig01_pdr_vs_n_snir_off.png": {"mode": {"snir_off"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig02_pdr_vs_n_snir_on.png": {"mode": {"snir_on"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig03_der_vs_n_snir_off.png": {"mode": {"snir_off"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig04_der_vs_n_snir_on.png": {"mode": {"snir_on"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig05_throughput_vs_n_snir_off.png": {"mode": {"snir_off"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig06_throughput_vs_n_snir_on.png": {"mode": {"snir_on"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig07_tc_vs_speed.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig08_fairness_vs_n.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig09_sf_distribution_snir_on.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig09b_sf_distribution_snir_on_small_multiples.png": {
            "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}
        },
        "fig10_sinr_cdf.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig11_airtime_vs_n.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig12_switch_count_vs_n.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig13_ucb_tracking_lag_vs_speed.png": {"algo": {"ucb", "ucb_forget"}},
        "fig14_reliability_airtime_pareto.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig15_outage_tail_prob_vs_n.png": {"mode": {"snir_on"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig16_fairness_reliability_tradeoff.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
    },
    "full": {
        "fig01_pdr_vs_n_snir_off.png": {"mode": {"snir_off"}},
        "fig02_pdr_vs_n_snir_on.png": {"mode": {"snir_on"}},
        "fig03_der_vs_n_snir_off.png": {"mode": {"snir_off"}},
        "fig04_der_vs_n_snir_on.png": {"mode": {"snir_on"}},
        "fig05_throughput_vs_n_snir_off.png": {"mode": {"snir_off"}},
        "fig06_throughput_vs_n_snir_on.png": {"mode": {"snir_on"}},
        "fig07_tc_vs_speed.png": {"speed": {"1", "3", "5"}},
        "fig08_fairness_vs_n.png": {"mode": {"snir_off", "snir_on"}},
        "fig09_sf_distribution_snir_on.png": {"mode": {"snir_on"}},
        "fig09b_sf_distribution_snir_on_small_multiples.png": {"mode": {"snir_on"}},
        "fig10_sinr_cdf.png": {"mode": {"snir_on"}},
        "fig11_airtime_vs_n.png": {"mode": {"snir_off", "snir_on"}},
        "fig12_switch_count_vs_n.png": {"mode": {"snir_off", "snir_on"}},
        "fig13_ucb_tracking_lag_vs_speed.png": {"algo": {"ucb", "ucb_forget"}, "speed": {"1", "3", "5"}},
        "fig14_reliability_airtime_pareto.png": {},
        "fig15_outage_tail_prob_vs_n.png": {"mode": {"snir_on"}, "speed": {"1", "3", "5"}},
        "fig16_fairness_reliability_tradeoff.png": {},
    },
}

FILTER_COLUMN_ALIASES = {"n": "N", "N": "N", "mode": "mode", "algo": "algo"}
MODE_VALUE_ALIASES = {
    "snir_off": "snir_off",
    "sniroff": "snir_off",
    "off": "snir_off",
    "snir_on": "snir_on",
    "sniron": "snir_on",
    "on": "snir_on",
}
ALGO_VALUE_ALIASES = {
    "adr": "adr",
    "adr_baseline": "adr",
    "adr_mixra": "adr_mixra",
    "adrmixra": "adr_mixra",
    "mixra": "adr_mixra",
    "ucb": "ucb",
    "ucb_forget": "ucb_forget",
    "ucbforget": "ucb_forget",
    "ucb_f": "ucb_forget",
}

METRIC_COLUMN_ALIASES = {
    "pdr_mean": ("pdr_mean", "pdr"),
    "der_mean": ("der_mean", "der"),
    "throughput_bps_mean": ("throughput_bps_mean", "throughput_mean_bps", "throughput_bps"),
    "jain_fairness_mean": ("jain_fairness_mean", "jain_fairness"),
    "airtime_total_s_mean": ("airtime_total_s_mean", "airtime_total_s"),
    "switch_count_mean": ("switch_count_mean", "switch_count"),
}


@dataclass(frozen=True)
class ScenarioFilters:
    by_column: dict[str, set[str]]

    @classmethod
    def from_tokens(cls, tokens: list[str] | None) -> "ScenarioFilters":
        mapping: dict[str, set[str]] = defaultdict(set)
        for token in tokens or []:
            if "=" not in token:
                warnings.warn(f"Filtre ignoré (format attendu clé=valeur1,valeur2): {token}", stacklevel=2)
                continue
            key, values = token.split("=", 1)
            key = key.strip()
            if not key:
                warnings.warn(f"Filtre ignoré (clé vide): {token}", stacklevel=2)
                continue
            key = FILTER_COLUMN_ALIASES.get(key, key)
            parsed = [item.strip() for item in values.split(",") if item.strip()]
            if not parsed:
                warnings.warn(f"Filtre ignoré (aucune valeur): {token}", stacklevel=2)
                continue
            mapping[key].update(_normalize_filter_value(key, value) for value in parsed)
        return cls(by_column=dict(mapping))

    def merge(self, extra: dict[str, set[str]]) -> "ScenarioFilters":
        merged = {key: set(values) for key, values in self.by_column.items()}
        for key, values in extra.items():
            if key in merged:
                merged[key] = merged[key].intersection(values)
            else:
                merged[key] = set(values)
        return ScenarioFilters(merged)


@dataclass(frozen=True)
class FigureTrace:
    figure: str
    source: str
    metric: str
    filters: dict[str, list[str]]
    num_points: int
    generated: bool


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        warnings.warn(f"Fichier agrégé manquant: {path}.", stacklevel=2)
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_aggregates_inputs(aggregates_dir: Path) -> list[str]:
    """Valide la présence des CSV et des colonnes contractuelles avant plotting."""

    errors: list[str] = []
    for key, filename in REQUIRED_FILES.items():
        csv_path = aggregates_dir / filename
        if not csv_path.is_file():
            errors.append(f"fichier manquant: {csv_path}")
            continue
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])

        expected = REQUIRED_COLUMNS.get(key, set())
        missing: list[str] = []
        for column in sorted(expected):
            candidates = METRIC_COLUMN_ALIASES.get(column, (column,))
            if not any(candidate in fieldnames for candidate in candidates):
                missing.append(column)

        if missing:
            errors.append(f"colonnes manquantes dans {csv_path.name}: {', '.join(missing)}")
    return errors


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    token = value.strip()
    if not token:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def _apply_filters(rows: list[dict[str, str]], filters: ScenarioFilters) -> list[dict[str, str]]:
    if not filters.by_column:
        return rows
    normalized_rows = [_normalize_row_for_filtering(row) for row in rows]
    filtered: list[dict[str, str]] = []
    for row in normalized_rows:
        keep = True
        for key, allowed in filters.by_column.items():
            if key not in row or row.get(key, "") not in allowed:
                keep = False
                break
        if keep:
            filtered.append(row)
    if rows and not filtered:
        filter_expr = _format_filters(filters)
        debug = ", ".join(_format_filter_availability(normalized_rows, filters))
        warnings.warn(
            f"Aucune ligne après filtrage. filtre={filter_expr}; lignes_candidates={len(rows)}. Détails: {debug}",
            stacklevel=2,
        )
    return filtered


def _normalize_filter_value(key: str, value: str) -> str:
    token = value.strip()
    normalized_token = token.lower().replace("-", "_")
    if key == "mode":
        return MODE_VALUE_ALIASES.get(normalized_token, normalized_token)
    if key == "algo":
        return ALGO_VALUE_ALIASES.get(normalized_token, normalized_token)
    if key == "N":
        try:
            return str(int(token))
        except ValueError:
            return token
    return token.lower()


def _normalize_row_for_filtering(row: dict[str, str]) -> dict[str, str]:
    normalized = dict(row)
    for raw_key, canonical_key in FILTER_COLUMN_ALIASES.items():
        if raw_key in normalized and canonical_key not in normalized:
            normalized[canonical_key] = normalized[raw_key]
    for key in ("mode", "algo", "N"):
        if key in normalized:
            normalized[key] = _normalize_filter_value(key, normalized.get(key, ""))
    return normalized


def _format_filter_availability(rows: list[dict[str, str]], filters: ScenarioFilters) -> list[str]:
    details: list[str] = []
    for key, allowed in filters.by_column.items():
        with_key = sum(1 for row in rows if key in row)
        matched = sum(1 for row in rows if row.get(key, "") in allowed)
        details.append(
            f"{key}∈{sorted(allowed)}: {matched}/{with_key} ligne(s) compatibles"
        )
    return details


def _format_filters(filters: ScenarioFilters) -> str:
    if not filters.by_column:
        return "<none>"
    return ";".join(f"{key}={','.join(sorted(values))}" for key, values in sorted(filters.by_column.items()))


def _filters_to_serializable(filters: ScenarioFilters) -> dict[str, list[str]]:
    return {key: sorted(values) for key, values in sorted(filters.by_column.items())}


def _resolve_profile_filter(article_profile: str, figure_name: str) -> dict[str, set[str]]:
    profile_filters = ARTICLE_PROFILE_FILTERS[article_profile]
    return {key: set(values) for key, values in profile_filters.get(figure_name, {}).items()}


def _warn_skip(fig_name: str, reason: str) -> None:
    warnings.warn(f"{fig_name} ignorée: {reason}", stacklevel=2)


def _algo_series(rows: list[dict[str, str]], *, fig_name: str) -> list[tuple[str, list[dict[str, str]]]]:
    normalized_rows = [_normalize_row_for_filtering(row) for row in rows]
    algos = sorted({row.get("algo", "").strip() for row in normalized_rows if row.get("algo", "").strip()})
    series: list[tuple[str, list[dict[str, str]]]] = []
    for algo in algos:
        algo_rows = [row for row in normalized_rows if row.get("algo", "").strip() == algo]
        if not algo_rows:
            warnings.warn(
                f"{fig_name}: série vide pour filtre exact algo={algo}. filtre=algo={algo}",
                stacklevel=2,
            )
            continue
        series.append((algo, algo_rows))
    return series


def _log_figure_result(path: Path, generated: bool, *, verbose: bool) -> None:
    if not verbose:
        return
    status = "générée" if generated else "ignorée"
    print(f"Figure {status}: {path}")

def _is_reliability_metric(y_col: str) -> bool:
    return y_col in {"pdr_mean", "der_mean"}


def _plot_xy_by_algo(
    rows: list[dict[str, str]], *, fig_name: str, y_col: str, out_path: Path, y_scale: str = "auto"
) -> bool:
    resolved_metric = _resolve_metric_column(rows, expected=y_col)
    needed = {"N", "algo", resolved_metric}
    if not rows:
        _warn_skip(fig_name, "aucune ligne disponible")
        return False
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    series = _algo_series(rows, fig_name=fig_name)
    if rows and not series:
        _warn_skip(fig_name, "aucune série après filtrage strict par algo")
        return False

    dropped = 0
    y_values: list[float] = []
    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo, algo_rows in series:
        per_x: dict[float, list[float]] = defaultdict(list)
        for row in algo_rows:
            x = _to_float(row.get("N"))
            y = _to_float(row.get(resolved_metric))
            if x is None or y is None:
                dropped += 1
                continue
            per_x[x].append(y)
        if not per_x:
            warnings.warn(
                f"{fig_name}: série algo vide après nettoyage numérique. filtre=algo={algo}",
                stacklevel=2,
            )
            continue

        xs = sorted(per_x)
        means: list[float] = []
        errors: list[float] = []
        for x in xs:
            ci = ci95_from_samples(per_x[x])
            if ci is None:
                continue
            means.append(ci.mean)
            errors.append(ci.half_width)
            y_values.append(ci.mean)
        if means:
            plt.errorbar(xs, means, yerr=errors, marker="o", capsize=3, label=algo)
            plotted += 1

    if dropped:
        warnings.warn(f"{fig_name}: {dropped} lignes ignorées (valeurs non numériques).", stacklevel=2)
    if plotted == 0:
        _warn_skip(fig_name, "aucune donnée traçable après nettoyage")
        plt.close()
        return False

    scale_policy = "standard"
    if _is_reliability_metric(y_col):
        y_min = min(y_values)
        y_max = max(y_values)
        if y_scale == "full":
            plt.ylim(0.0, 1.0)
            scale_policy = "full [0,1]"
        elif y_scale == "zoom":
            lower = max(0.0, y_min - 0.02)
            upper = min(1.0, max(y_max + 0.01, lower + 0.01))
            plt.ylim(lower, upper)
            scale_policy = f"zoom [{lower:.3f},{upper:.3f}]"
        elif y_scale == "auto":
            if y_min >= 0.9:
                lower = max(0.0, y_min - 0.02)
                upper = min(1.0, max(y_max + 0.01, lower + 0.01))
                plt.ylim(lower, upper)
                scale_policy = f"auto→zoom [{lower:.3f},{upper:.3f}] + annexe [0,1]"
            else:
                plt.ylim(0.0, 1.0)
                scale_policy = "auto→full [0,1]"

    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("N"))
    plt.ylabel(normalized_axis_label(y_col))
    plt.legend(title=f"Algo | y-scale: {scale_policy}")
    plt.tight_layout()
    _save_figure_variants(out_path)

    if _is_reliability_metric(y_col) and y_scale == "auto" and y_values and min(y_values) >= 0.9:
        plt.ylim(0.0, 1.0)
        plt.legend(title="Algo | y-scale: annexe full [0,1]")
        plt.tight_layout()
        annex_path = out_path.with_name(f"{out_path.stem}_annex_full_scale{out_path.suffix}")
        _save_figure_variants(annex_path)

    plt.close()
    return True


def _save_figure_variants(out_path: Path) -> None:
    png_path = out_path.with_suffix(".png")
    pdf_path = out_path.with_suffix(".pdf")
    plt.savefig(png_path, dpi=PLOT_DPI)
    plt.savefig(pdf_path)


def _stable_figure_name(filename: str) -> str:
    stem = Path(filename).stem
    if stem.startswith("fig") and len(stem) >= 5 and stem[3:5].isdigit():
        return f"{stem[:5]}_{stem[6:] if len(stem) > 6 and stem[5] == '_' else stem[5:]}.png"
    return filename


def _count_points(rows: list[dict[str, str]], metric: str) -> int:
    resolved = _resolve_metric_column(rows, expected=metric)
    if not rows:
        return 0
    if metric == "sinr_db":
        return sum(1 for row in rows if _to_float(row.get("sinr_db")) is not None and _to_float(row.get("quantile")) is not None)
    if metric == "ratio":
        return sum(1 for row in rows if _to_float(row.get("sf")) is not None and _to_float(row.get("ratio")) is not None)
    if metric == "Tc_s":
        return sum(1 for row in rows if _to_float(row.get("speed")) is not None and _to_float(row.get("Tc_s")) is not None)
    return sum(1 for row in rows if _to_float(row.get("N")) is not None and _to_float(row.get(resolved)) is not None)


def _resolve_metric_column(rows: list[dict[str, str]], *, expected: str) -> str:
    if not rows:
        return expected
    for candidate in METRIC_COLUMN_ALIASES.get(expected, (expected,)):
        if candidate in rows[0]:
            if candidate != expected:
                warnings.warn(
                    f"Colonne '{expected}' absente, repli sur '{candidate}' (compatibilité agrégats).",
                    stacklevel=3,
                )
            return candidate
    return expected


def _plot_tc_vs_speed(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "fichier convergence_tc.csv vide ou absent")
        return False
    tc_column = "Tc_s_mean" if rows and "Tc_s_mean" in rows[0] else "Tc_s"
    needed = {"speed", "algo", tc_column}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    series = _algo_series(rows, fig_name=fig_name)
    if not series:
        _warn_skip(fig_name, "pas de couples speed/Tc_s exploitables")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo, algo_rows in series:
        grouped: dict[float, list[float]] = defaultdict(list)
        for row in algo_rows:
            speed = _to_float(row.get("speed"))
            tc_s = _to_float(row.get(tc_column))
            if speed is None or tc_s is None:
                continue
            grouped[speed].append(tc_s)
        if not grouped:
            warnings.warn(f"{fig_name}: série algo vide après filtre exact. filtre=algo={algo}", stacklevel=2)
            continue

        speeds = sorted(grouped)
        means: list[float] = []
        errors: list[float] = []
        for speed in speeds:
            ci = ci95_from_samples(grouped[speed])
            if ci is None:
                continue
            means.append(ci.mean)
            errors.append(ci.half_width)
        if means:
            plt.errorbar(speeds, means, yerr=errors, marker="o", capsize=3, label=algo)
            plotted += 1
    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "pas de couples speed/Tc_s exploitables")
        return False
    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("speed"))
    plt.ylabel(normalized_axis_label("Tc_s"))
    plt.legend()
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_sinr_cdf(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "fichier sinr_cdf.csv vide ou absent")
        return False
    needed = {"algo", "mode", "N", "speed", "quantile", "sinr_db"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    by_group: dict[tuple[str, str, str, str], list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        q = _to_float(row.get("quantile"))
        sinr = _to_float(row.get("sinr_db"))
        if q is None or sinr is None:
            continue
        algo = row.get("algo", "unknown")
        mode = row.get("mode", "")
        n = row.get("N", "")
        speed = row.get("speed", "")
        by_group[(algo, mode, n, speed)].append((q, sinr))

    if not by_group:
        _warn_skip(fig_name, "pas de points quantile/sinr exploitables")
        return False

    by_algo: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for (algo, mode, n, speed), points in sorted(by_group.items()):
        points.sort(key=lambda item: (item[0], item[1]))
        quantiles = [item[0] for item in points]
        sinrs = [item[1] for item in points]
        if any(q <= 0.0 or q > 1.0 for q in quantiles):
            _warn_skip(fig_name, f"quantile hors ]0..1] pour groupe algo={algo}, mode={mode}, N={n}, speed={speed}")
            plt.close()
            return False
        if any(curr < prev for prev, curr in zip(quantiles, quantiles[1:], strict=False)):
            _warn_skip(fig_name, f"quantile non monotone croissant pour groupe algo={algo}, mode={mode}, N={n}, speed={speed}")
            plt.close()
            return False
        if any(curr < prev for prev, curr in zip(sinrs, sinrs[1:], strict=False)):
            _warn_skip(fig_name, f"sinr_db non monotone croissant pour groupe algo={algo}, mode={mode}, N={n}, speed={speed}")
            plt.close()
            return False
        if sinrs[-1] <= sinrs[0]:
            _warn_skip(fig_name, f"étendue SINR nulle pour groupe algo={algo}, mode={mode}, N={n}, speed={speed}")
            plt.close()
            return False

        by_algo[algo].extend(points)

    if not by_algo:
        _warn_skip(fig_name, "aucune courbe CDF traçable")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo, points in sorted(by_algo.items()):
        points.sort(key=lambda item: (item[0], item[1]))
        by_quantile: dict[float, list[float]] = defaultdict(list)
        for quantile, sinr in points:
            by_quantile[quantile].append(sinr)
        quantiles = sorted(by_quantile)
        mean_sinrs = [sum(by_quantile[q]) / len(by_quantile[q]) for q in quantiles]

        if any(curr <= prev for prev, curr in zip(quantiles, quantiles[1:], strict=False)):
            _warn_skip(fig_name, f"quantile non monotone croissant pour algo={algo}")
            plt.close()
            return False
        if mean_sinrs and all(value == mean_sinrs[0] for value in mean_sinrs[1:]):
            _warn_skip(fig_name, f"sinr_db constant sur tout le groupe pour algo={algo}")
            plt.close()
            return False

        plt.plot(mean_sinrs, quantiles, label=algo)
        plotted += 1

    if plotted == 0:
        _warn_skip(fig_name, "aucune courbe CDF traçable")
        plt.close()
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("sinr_db"))
    plt.ylabel(normalized_axis_label("quantile"))
    plt.legend()
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_sf_distribution(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "fichier distribution_sf.csv vide ou absent")
        return False
    needed = {"sf", "algo"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False
    if "ratio" not in rows[0] and "count" not in rows[0]:
        _warn_skip(fig_name, "colonnes manquantes ['ratio' ou 'count']")
        return False

    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    has_ratio = "ratio" in rows[0]
    for row in rows:
        sf = _to_float(row.get("sf"))
        value = _to_float(row.get("ratio")) if has_ratio else _to_float(row.get("count"))
        if sf is None or value is None:
            continue
        sf_int = int(sf)
        if sf_int < 7 or sf_int > 12:
            continue
        grouped[row.get("algo", "unknown")][sf_int].append(value)

    if not grouped:
        _warn_skip(fig_name, "pas de points SF/ratio exploitables")
        return False

    sf_values = list(range(7, 13))
    algos = sorted(grouped)

    data_percent: dict[str, list[float]] = {}
    for algo in algos:
        means = {sf: sum(grouped[algo][sf]) / len(grouped[algo][sf]) for sf in grouped[algo]}
        ordered = [max(0.0, means.get(sf, 0.0)) for sf in sf_values]
        if has_ratio:
            total = sum(ordered)
            if total > 0 and total > 1.5:
                ordered = [value / total for value in ordered]
        else:
            total = sum(ordered)
            if total > 0:
                ordered = [value / total for value in ordered]
        data_percent[algo] = [value * 100.0 for value in ordered]

    x_positions = list(range(len(sf_values)))
    y_ticks = list(range(0, 101, 10))

    width = 0.8 / max(len(algos), 1)
    plt.figure(figsize=(10, 5))
    for idx, algo in enumerate(algos):
        offset = (idx - (len(algos) - 1) / 2) * width
        xs = [x + offset for x in x_positions]
        plt.bar(xs, data_percent[algo], width=width, label=algo)
    plt.grid(axis="y", alpha=0.3)
    plt.xlabel(normalized_axis_label("sf"))
    plt.ylabel(normalized_axis_label("ratio"))
    plt.xticks(x_positions, [str(sf) for sf in sf_values])
    plt.ylim(0, 100)
    plt.yticks(y_ticks)
    plt.legend(title="Algo", ncols=2)
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_sf_distribution_small_multiples(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "fichier distribution_sf.csv vide ou absent")
        return False
    needed = {"sf", "algo"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False
    if "ratio" not in rows[0] and "count" not in rows[0]:
        _warn_skip(fig_name, "colonnes manquantes ['ratio' ou 'count']")
        return False

    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    has_ratio = "ratio" in rows[0]
    for row in rows:
        sf = _to_float(row.get("sf"))
        value = _to_float(row.get("ratio")) if has_ratio else _to_float(row.get("count"))
        if sf is None or value is None:
            continue
        sf_int = int(sf)
        if sf_int < 7 or sf_int > 12:
            continue
        grouped[row.get("algo", "unknown")][sf_int].append(value)

    if not grouped:
        _warn_skip(fig_name, "pas de points SF/ratio exploitables")
        return False

    sf_values = list(range(7, 13))
    algos = sorted(grouped)
    data_percent: dict[str, list[float]] = {}
    for algo in algos:
        means = {sf: sum(grouped[algo][sf]) / len(grouped[algo][sf]) for sf in grouped[algo]}
        ordered = [max(0.0, means.get(sf, 0.0)) for sf in sf_values]
        total = sum(ordered)
        if total > 0:
            ordered = [value / total for value in ordered]
        data_percent[algo] = [value * 100.0 for value in ordered]

    x_positions = list(range(len(sf_values)))
    y_ticks = list(range(0, 101, 10))
    fig, axes = plt.subplots(len(algos), 1, figsize=(9, 2.8 * len(algos)), sharex=True, sharey=True)
    if hasattr(axes, "ravel"):
        axes_list = list(axes.ravel())
    elif isinstance(axes, (list, tuple)):
        axes_list = list(axes)
    else:
        axes_list = [axes]

    for axis, algo in zip(axes_list, algos, strict=False):
        axis.bar(x_positions, data_percent[algo], width=0.7, label=algo)
        axis.grid(axis="y", alpha=0.3)
        axis.set_ylim(0, 100)
        axis.set_yticks(y_ticks)
        axis.legend(loc="upper right", title="Algo")

    axes_list[-1].set_xticks(x_positions, [str(sf) for sf in sf_values])
    axes_list[-1].set_xlabel(normalized_axis_label("sf"))
    fig.supylabel(normalized_axis_label("ratio"))
    fig.tight_layout()
    fig.savefig(out_path.with_suffix(".png"), dpi=PLOT_DPI)
    fig.savefig(out_path.with_suffix(".pdf"))
    plt.close(fig)
    return True


def _plot_delta_pdr_on_minus_off(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "aucune ligne disponible")
        return False
    pdr_col = _resolve_metric_column(rows, expected="pdr_mean")
    needed = {"N", "algo", "mode", pdr_col}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    by_mode: dict[str, dict[float, dict[str, list[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in rows:
        n_value = _to_float(row.get("N"))
        pdr = _to_float(row.get(pdr_col))
        mode = row.get("mode", "")
        if n_value is None or pdr is None or mode not in {"snir_on", "snir_off"}:
            continue
        by_mode[row.get("algo", "unknown")][n_value][mode].append(pdr)

    if not by_mode:
        _warn_skip(fig_name, "aucune paire N/algo exploitable")
        return False

    plt.figure(figsize=(8, 5))
    for algo in sorted(by_mode):
        xs: list[float] = []
        means: list[float] = []
        errors: list[float] = []
        for n_value in sorted(by_mode[algo]):
            pair = by_mode[algo][n_value]
            on_samples = pair.get("snir_on", [])
            off_samples = pair.get("snir_off", [])
            if not on_samples or not off_samples:
                continue
            ci_on = ci95_from_samples(on_samples)
            ci_off = ci95_from_samples(off_samples)
            if ci_on is None or ci_off is None:
                continue
            xs.append(n_value)
            means.append(ci_on.mean - ci_off.mean)
            errors.append((ci_on.half_width**2 + ci_off.half_width**2) ** 0.5)
        if xs:
            plt.errorbar(xs, means, yerr=errors, marker="o", capsize=3, label=algo)

    if not plt.gca().lines:
        plt.close()
        _warn_skip(fig_name, "aucune paire SNIR_ON/SNIR_OFF alignée")
        return False

    plt.axhline(0.0, color="black", linewidth=1.0, linestyle="--", alpha=0.6)
    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("N"))
    plt.ylabel("ΔPDR (SNIR_ON - SNIR_OFF) [-]")
    plt.legend()
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _duration_hours_from_row(row: dict[str, str]) -> float:
    hours = _to_float(row.get("duration_h") or row.get("duration_hours") or row.get("simulation_hours"))
    if hours is not None and hours > 0:
        return hours
    seconds = _to_float(row.get("duration_s") or row.get("sim_time_s") or row.get("steps"))
    if seconds is not None and seconds > 0:
        return seconds / 3600.0
    return 1.0


def _plot_switching_vs_speed(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "aucune ligne disponible")
        return False
    switch_col = _resolve_metric_column(rows, expected="switch_count_mean")
    needed = {"speed", "algo", switch_col}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    grouped: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        speed = _to_float(row.get("speed"))
        switch_count = _to_float(row.get(switch_col))
        if speed is None or switch_count is None:
            continue
        grouped[row.get("algo", "unknown")][speed].append(switch_count / _duration_hours_from_row(row))

    if not grouped:
        _warn_skip(fig_name, "pas de couples speed/switch_count exploitables")
        return False

    plt.figure(figsize=(8, 5))
    for algo in sorted(grouped):
        speeds = sorted(grouped[algo])
        means: list[float] = []
        errors: list[float] = []
        for speed in speeds:
            ci = ci95_from_samples(grouped[algo][speed])
            if ci is None:
                continue
            means.append(ci.mean)
            errors.append(ci.half_width)
        plt.errorbar(speeds, means, yerr=errors, marker="o", capsize=3, label=algo)

    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("speed"))
    plt.ylabel("Instabilité [switch_count/h]")
    plt.legend()
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True




def _plot_ucb_tracking_lag_vs_speed(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "fichier ucb_tracking.csv vide ou absent")
        return False
    tc_column = "Tc_s_mean" if rows and "Tc_s_mean" in rows[0] else "Tc_s"
    needed = {"speed", "algo", tc_column}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    series = _algo_series(rows, fig_name=fig_name)
    if not series:
        _warn_skip(fig_name, "pas de couples speed/Tc_s exploitables")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo, algo_rows in series:
        grouped: dict[float, list[float]] = defaultdict(list)
        for row in algo_rows:
            speed = _to_float(row.get("speed"))
            tc_s = _to_float(row.get(tc_column))
            if speed is None or tc_s is None:
                continue
            grouped[speed].append(tc_s)
        if not grouped:
            warnings.warn(f"{fig_name}: série algo vide après filtre exact. filtre=algo={algo}", stacklevel=2)
            continue

        speeds = sorted(grouped)
        means: list[float] = []
        errors: list[float] = []
        for speed in speeds:
            ci = ci95_from_samples(grouped[speed])
            if ci is None:
                continue
            means.append(ci.mean)
            errors.append(ci.half_width)
        if means:
            plt.errorbar(speeds, means, yerr=errors, marker="o", capsize=3, label=algo)
            plotted += 1
    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "pas de couples speed/Tc_s exploitables")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("speed"))
    plt.ylabel("Délai de ré-adaptation Tc [s]")
    plt.legend(title="Algo")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_outage_tail_prob_vs_n(rows: list[dict[str, str]], out_path: Path, *, threshold_db: float = -10.0) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "fichier sinr_cdf.csv vide ou absent")
        return False
    needed = {"algo", "N", "sinr_db", "quantile"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    grouped: dict[str, dict[float, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        algo = row.get("algo", "unknown")
        n_value = _to_float(row.get("N"))
        sinr = _to_float(row.get("sinr_db"))
        quantile = _to_float(row.get("quantile"))
        if n_value is None or sinr is None or quantile is None:
            continue
        grouped[algo][n_value].append((sinr, quantile))

    if not grouped:
        _warn_skip(fig_name, "aucun point SINR/quantile exploitable")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo in sorted(grouped):
        xs: list[float] = []
        ys: list[float] = []
        for n_value in sorted(grouped[algo]):
            points = sorted(grouped[algo][n_value], key=lambda pair: pair[0])
            cands = [q for sinr, q in points if sinr <= threshold_db]
            if not cands:
                continue
            xs.append(n_value)
            ys.append(max(0.0, min(1.0, max(cands))))
        if xs:
            plt.plot(xs, ys, marker="o", label=algo)
            plotted += 1

    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, f"aucune estimation P[SINR<{threshold_db:g} dB] traçable")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("N"))
    plt.ylabel(f"P[SINR < {threshold_db:g} dB]")
    plt.ylim(0, 1)
    plt.legend(title="Algo")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_fairness_reliability_tradeoff(rows: list[dict[str, str]], out_path: Path) -> bool:
    """Un seul message scientifique: comparaison des moyennes (±IC95) fairness vs PDR par algo."""

    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "aucune ligne disponible")
        return False
    pdr_col = _resolve_metric_column(rows, expected="pdr_mean")
    fairness_col = _resolve_metric_column(rows, expected="jain_fairness_mean")
    needed = {"algo", pdr_col, fairness_col}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        pdr = _to_float(row.get(pdr_col))
        fairness = _to_float(row.get(fairness_col))
        if pdr is None or fairness is None:
            continue
        grouped[row.get("algo", "unknown")].append((fairness, pdr))

    if not grouped:
        _warn_skip(fig_name, "pas de couples fairness/PDR exploitables")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo in sorted(grouped):
        xs = [pair[0] for pair in grouped[algo]]
        ys = [pair[1] for pair in grouped[algo]]
        ci_x = ci95_from_samples(xs)
        ci_y = ci95_from_samples(ys)
        if ci_x is None or ci_y is None:
            continue
        plt.errorbar(
            [ci_x.mean],
            [ci_y.mean],
            xerr=[ci_x.half_width],
            yerr=[ci_y.half_width],
            fmt="o",
            markersize=7,
            capsize=4,
            label=algo,
        )
        plotted += 1

    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "aucun point moyen±IC95 traçable")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("jain_fairness_mean"))
    plt.ylabel(normalized_axis_label("pdr_mean"))
    plt.xlim(0, 1.05)
    plt.ylim(0, 1.05)
    plt.legend(title="Algo")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True
def _plot_airtime_reliability_pareto(rows: list[dict[str, str]], out_path: Path) -> bool:
    """Un seul message scientifique: compromis moyen airtime vs PDR par algo."""

    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "aucune ligne disponible")
        return False
    pdr_col = _resolve_metric_column(rows, expected="pdr_mean")
    airtime_col = _resolve_metric_column(rows, expected="airtime_total_s_mean")
    needed = {"algo", pdr_col, airtime_col}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        pdr = _to_float(row.get(pdr_col))
        airtime = _to_float(row.get(airtime_col))
        if pdr is None or airtime is None:
            continue
        grouped[row.get("algo", "unknown")].append((airtime, pdr))

    if not grouped:
        _warn_skip(fig_name, "pas de couples airtime/PDR exploitables")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo in sorted(grouped):
        xs = [pair[0] for pair in grouped[algo]]
        ys = [pair[1] for pair in grouped[algo]]
        ci_x = ci95_from_samples(xs)
        ci_y = ci95_from_samples(ys)
        if ci_x is None or ci_y is None:
            continue
        plt.errorbar(
            [ci_x.mean],
            [ci_y.mean],
            xerr=[ci_x.half_width],
            yerr=[ci_y.half_width],
            fmt="o",
            markersize=7,
            capsize=4,
            label=algo,
        )
        plotted += 1

    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "aucun point moyen±IC95 traçable")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(normalized_axis_label("airtime_total_s_mean"))
    plt.ylabel(normalized_axis_label("pdr_mean"))
    plt.legend(title="Algo")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def generate_minimal_figures(
    *,
    aggregates_dir: Path,
    out_dir: Path,
    filters: ScenarioFilters,
    article_profile: str = "core",
    include_bonus: bool = True,
    verbose: bool = False,
    ieee_ready: bool = False,
    y_scale: str = "auto",
) -> tuple[list[Path], list[FigureTrace]]:
    if article_profile not in ARTICLE_PROFILE_FILTERS:
        raise ValueError(f"Profil article inconnu: {article_profile}")

    setup_plot_style(ieee_ready=ieee_ready)
    out_dir.mkdir(parents=True, exist_ok=True)
    payloads = {name: _read_csv_rows(aggregates_dir / filename) for name, filename in REQUIRED_FILES.items()}

    generated: list[Path] = []
    traces: list[FigureTrace] = []

    for fig_name, source, metric, local_filter in FIGURE_SPECS:
        effective_filters = filters.merge(local_filter).merge(_resolve_profile_filter(article_profile, fig_name))
        selected = _apply_filters(payloads[source], effective_filters)
        out_path = out_dir / _stable_figure_name(fig_name)
        did_generate = _plot_xy_by_algo(selected, fig_name=fig_name, y_col=metric, out_path=out_path, y_scale=y_scale)
        traces.append(
            FigureTrace(
                figure=out_path.name,
                source=source,
                metric=metric,
                filters=_filters_to_serializable(effective_filters),
                num_points=_count_points(selected, metric),
                generated=did_generate,
            )
        )
        _log_figure_result(out_path, did_generate, verbose=verbose)
        if did_generate:
            generated.append(out_path)

    fig07 = out_dir / _stable_figure_name("fig07_tc_vs_speed.png")
    fig07_filters = filters.merge(_resolve_profile_filter(article_profile, fig07.name))
    did_generate = _plot_tc_vs_speed(_apply_filters(payloads["convergence_tc"], fig07_filters), fig07)
    traces.append(
        FigureTrace(
            figure=fig07.name,
            source="convergence_tc",
            metric="Tc_s",
            filters=_filters_to_serializable(fig07_filters),
            num_points=_count_points(_apply_filters(payloads["convergence_tc"], fig07_filters), "Tc_s"),
            generated=did_generate,
        )
    )
    _log_figure_result(fig07, did_generate, verbose=verbose)
    if did_generate:
        generated.append(fig07)

    fig08 = out_dir / _stable_figure_name("fig08_fairness_vs_n.png")
    fig08_filters = filters.merge(_resolve_profile_filter(article_profile, fig08.name))
    did_generate = _plot_xy_by_algo(
        _apply_filters(payloads["metric_by_factor"], fig08_filters),
        fig_name=fig08.name,
        y_col="jain_fairness_mean",
        out_path=fig08,
        y_scale=y_scale,
    )
    traces.append(
        FigureTrace(
            figure=fig08.name,
            source="metric_by_factor",
            metric="jain_fairness_mean",
            filters=_filters_to_serializable(fig08_filters),
            num_points=_count_points(_apply_filters(payloads["metric_by_factor"], fig08_filters), "jain_fairness_mean"),
            generated=did_generate,
        )
    )
    _log_figure_result(fig08, did_generate, verbose=verbose)
    if did_generate:
        generated.append(fig08)

    fig09 = out_dir / _stable_figure_name("fig09_sf_distribution_snir_on.png")
    fig09_filters = filters.merge(_resolve_profile_filter(article_profile, fig09.name))
    did_generate = _plot_sf_distribution(_apply_filters(payloads["distribution_sf"], fig09_filters), fig09)
    traces.append(
        FigureTrace(
            figure=fig09.name,
            source="distribution_sf",
            metric="ratio",
            filters=_filters_to_serializable(fig09_filters),
            num_points=_count_points(_apply_filters(payloads["distribution_sf"], fig09_filters), "ratio"),
            generated=did_generate,
        )
    )
    _log_figure_result(fig09, did_generate, verbose=verbose)
    if did_generate:
        generated.append(fig09)

    fig09b = out_dir / _stable_figure_name("fig09b_sf_distribution_snir_on_small_multiples.png")
    fig09b_filters = filters.merge(_resolve_profile_filter(article_profile, fig09b.name))
    did_generate = _plot_sf_distribution_small_multiples(_apply_filters(payloads["distribution_sf"], fig09b_filters), fig09b)
    traces.append(
        FigureTrace(
            figure=fig09b.name,
            source="distribution_sf",
            metric="ratio",
            filters=_filters_to_serializable(fig09b_filters),
            num_points=_count_points(_apply_filters(payloads["distribution_sf"], fig09b_filters), "ratio"),
            generated=did_generate,
        )
    )
    _log_figure_result(fig09b, did_generate, verbose=verbose)
    if did_generate:
        generated.append(fig09b)

    fig10 = out_dir / _stable_figure_name("fig10_sinr_cdf.png")
    fig10_filters = filters.merge(_resolve_profile_filter(article_profile, fig10.name))
    did_generate = _plot_sinr_cdf(_apply_filters(payloads["sinr_cdf"], fig10_filters), fig10)
    traces.append(
        FigureTrace(
            figure=fig10.name,
            source="sinr_cdf",
            metric="sinr_db",
            filters=_filters_to_serializable(fig10_filters),
            num_points=_count_points(_apply_filters(payloads["sinr_cdf"], fig10_filters), "sinr_db"),
            generated=did_generate,
        )
    )
    _log_figure_result(fig10, did_generate, verbose=verbose)
    if did_generate:
        generated.append(fig10)

    if include_bonus:
        for fig_name, source, metric, local_filter in BONUS_SPECS:
            effective_filters = filters.merge(local_filter).merge(_resolve_profile_filter(article_profile, fig_name))
            selected = _apply_filters(payloads[source], effective_filters)
            out_path = out_dir / _stable_figure_name(fig_name)
            if fig_name == "fig13_ucb_tracking_lag_vs_speed.png":
                did_generate = _plot_ucb_tracking_lag_vs_speed(selected, out_path)
            elif fig_name == "fig14_reliability_airtime_pareto.png":
                did_generate = _plot_airtime_reliability_pareto(selected, out_path)
            elif fig_name == "fig15_outage_tail_prob_vs_n.png":
                did_generate = _plot_outage_tail_prob_vs_n(selected, out_path)
            elif fig_name == "fig16_fairness_reliability_tradeoff.png":
                did_generate = _plot_fairness_reliability_tradeoff(selected, out_path)
            else:
                did_generate = _plot_xy_by_algo(selected, fig_name=fig_name, y_col=metric, out_path=out_path, y_scale=y_scale)
            traces.append(
                FigureTrace(
                    figure=out_path.name,
                    source=source,
                    metric=metric,
                    filters=_filters_to_serializable(effective_filters),
                    num_points=_count_points(selected, metric),
                    generated=did_generate,
                )
            )
            _log_figure_result(out_path, did_generate, verbose=verbose)
            if did_generate:
                generated.append(out_path)

    manifest_path = out_dir / "plots_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["figure", "source", "filtre", "date", "nb_points"])
        writer.writeheader()
        for trace in traces:
            writer.writerow(
                {
                    "figure": trace.figure,
                    "source": REQUIRED_FILES.get(trace.source, trace.source),
                    "filtre": json.dumps(trace.filters, ensure_ascii=False, sort_keys=True),
                    "nb_points": trace.num_points,
                    "date": datetime.now(timezone.utc).isoformat(),
                }
            )

    summary_payload = {
        "article_profile": article_profile,
        "requested_filters": _filters_to_serializable(filters),
        "figures": [
            {
                "figure": trace.figure,
                "source": trace.source,
                "metric": trace.metric,
                "filters": trace.filters,
                "num_points": trace.num_points,
                "generated": trace.generated,
            }
            for trace in traces
        ],
    }
    (out_dir / "plots_summary.json").write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return generated, traces


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Génère les figures fig01..fig10 (et bonus fig11..fig16) depuis aggregates/*.csv")
    parser.add_argument("--aggregates-dir", required=True, type=Path, help="Répertoire contenant les CSV agrégés.")
    parser.add_argument("--out", required=True, type=Path, help="Répertoire cible pour les PNG.")
    parser.add_argument(
        "--scenario-filter",
        action="append",
        default=[],
        help="Filtre clé=val1,val2 (répétable), ex: --scenario-filter mode=snir_on --scenario-filter algo=ucb,legacy",
    )
    parser.add_argument("--no-bonus", action="store_true", help="N'écrit pas les figures bonus fig11..fig16.")
    parser.add_argument("--ieee-ready", action="store_true", help="Active le style IEEE (couleurs daltonisme-friendly, linewidths, export PDF+PNG).")
    parser.add_argument(
        "--article-profile",
        choices=sorted(ARTICLE_PROFILE_FILTERS),
        default="core",
        help="Profil d'article figé pour imposer les filtres documentés par figure (core ou full).",
    )
    parser.add_argument(
        "--y-scale",
        choices=["auto", "full", "zoom"],
        default="auto",
        help="Politique d'échelle Y pour PDR/DER: auto (zoom si proche de 1 + annexe full), full ([0,1]), zoom.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated, _ = generate_minimal_figures(
        aggregates_dir=args.aggregates_dir,
        out_dir=args.out,
        filters=ScenarioFilters.from_tokens(args.scenario_filter),
        article_profile=args.article_profile,
        include_bonus=not args.no_bonus,
        ieee_ready=args.ieee_ready,
        y_scale=args.y_scale,
    )
    print(f"{len(generated)} figure(s) générée(s).")
    for path in generated:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

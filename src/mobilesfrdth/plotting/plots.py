"""Generate figures from ``aggregates/*.csv`` only."""

from __future__ import annotations

import argparse
import csv
import json
import random
import warnings
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
from matplotlib.patches import Ellipse

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .utils import ci95_from_samples, normalized_axis_label, setup_plot_style, PLOT_DPI


AXIS_LABELS_EN = {
    "N": "Number of nodes N",
    "speed": "Speed (m/s)",
    "pdr_mean": "Packet Delivery Ratio",
    "der_mean": "Data Extraction Ratio",
    "throughput_bps_mean": "Throughput (bit/s)",
    "outage_prob_mean": "Outage probability",
    "jain_fairness_mean": "Jain's fairness index (unitless)",
    "airtime_total_s_mean": "Total airtime (s)",
    "switch_count_mean": "Number of switches",
    "Tc_s": "Convergence time Tc (s)",
    "adaptation_cost": "Adaptation cost (switch_count + Tc)",
    "sinr_db": "SINR (dB)",
    "quantile": "Cumulative probability",
    "sf": "Spreading Factor",
    "ratio": "Usage share (%)",
}


@dataclass(frozen=True)
class AlgoStyle:
    color: str
    marker: str
    linestyle: str


ALGO_STYLE: dict[str, AlgoStyle] = {
    "adr": AlgoStyle(color="#1f77b4", marker="o", linestyle="-"),
    "adr_mixra": AlgoStyle(color="#ff7f0e", marker="s", linestyle="--"),
    "ucb": AlgoStyle(color="#2ca02c", marker="^", linestyle="-."),
    "ucb_forget": AlgoStyle(color="#d62728", marker="D", linestyle=":"),
}


def _algo_style_kwargs(algo: str) -> dict[str, str]:
    style = ALGO_STYLE.get(algo)
    if style is None:
        return {"marker": "o", "linestyle": "-"}
    return {"color": style.color, "marker": style.marker, "linestyle": style.linestyle}


def _axis_label(name: str) -> str:
    return AXIS_LABELS_EN.get(name, normalized_axis_label(name))


def _add_compact_legend(*, title: str = "Algorithm") -> None:
    plt.legend(title=title, fontsize=8, title_fontsize=9, ncols=2, frameon=False, handlelength=1.5)


REQUIRED_FILES = {
    "metric_by_factor": "metric_by_factor.csv",
    "distribution_sf": "distribution_sf.csv",
    "convergence_tc": "convergence_tc.csv",
    "sinr_cdf": "sinr_cdf.csv",
    "fairness_airtime_switching": "fairness_airtime_switching.csv",
    "ucb_tracking": "ucb_tracking.csv",
    "pareto_reliability_airtime": "pareto_reliability_airtime.csv",
    "outage_probability": "outage_probability.csv",
    "energy_efficiency_reliability": "energy_efficiency_reliability.csv",
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
    "sinr_cdf": {"algo", "mode", "N", "speed", "mobility_model", "gateways", "sigma", "quantile", "sinr_db"},
    "fairness_airtime_switching": {"N", "algo", "jain_fairness", "airtime_total_s", "switch_count"},
    "ucb_tracking": {"speed", "mode", "algo", "Tc_s_mean"},
    "pareto_reliability_airtime": {"algo", "pdr_mean", "pdr_ci95", "airtime_total_s_mean", "airtime_total_s_ci95"},
    "outage_probability": {"N", "algo", "mode", "outage_prob_mean", "outage_prob_ci95"},
    "energy_efficiency_reliability": {
        "algo",
        "pdr_mean",
        "pdr_ci95",
        "energy_efficiency_mean",
        "energy_efficiency_ci95",
    },
}

FIGURE_SPECS = [
    ("fig01_pdr_vs_n_snir_off.png", "metric_by_factor", "pdr_mean", {"mode": {"snir_off"}}),
    ("fig02_pdr_vs_n_snir_on.png", "metric_by_factor", "pdr_mean", {"mode": {"snir_on"}}),
    ("fig03_der_vs_n_snir_off.png", "metric_by_factor", "der_mean", {"mode": {"snir_off"}}),
    ("fig04_der_vs_n_snir_on.png", "metric_by_factor", "der_mean", {"mode": {"snir_on"}}),
    ("fig05_throughput_vs_n_snir_off.png", "metric_by_factor", "throughput_bps_mean", {"mode": {"snir_off"}}),
    ("fig06_throughput_vs_n_snir_on.png", "metric_by_factor", "throughput_bps_mean", {"mode": {"snir_on"}}),
]

CONTRIBUTION_SPECS = [
    ("fig08_outage_probability_vs_n.png", "outage_probability", "outage_prob_mean", {}),
    ("fig09_energy_efficiency_vs_pdr_pareto.png", "energy_efficiency_reliability", "pdr_mean", {}),
    ("fig10_sinr_cdf_fixed_scenario.png", "sinr_cdf", "sinr_db", {}),
    ("fig11_adaptation_cost_vs_speed.png", "metric_by_factor", "adaptation_cost", {}),
]

ARTICLE_PROFILE_FILTERS: dict[str, dict[str, dict[str, set[str]]]] = {
    "core": {
        "fig01_pdr_vs_n_snir_off.png": {"mode": {"snir_off"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig02_pdr_vs_n_snir_on.png": {"mode": {"snir_on"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig03_der_vs_n_snir_off.png": {"mode": {"snir_off"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig04_der_vs_n_snir_on.png": {"mode": {"snir_on"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig05_throughput_vs_n_snir_off.png": {"mode": {"snir_off"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig06_throughput_vs_n_snir_on.png": {"mode": {"snir_on"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig07_sf_histogram_by_algo.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig08_outage_probability_vs_n.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig09_energy_efficiency_vs_pdr_pareto.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig10_sinr_cdf_fixed_scenario.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig11_adaptation_cost_vs_speed.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
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
        "fig14_pareto_reliability_airtime.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig15_outage_probability_vs_n.png": {"mode": {"snir_on"}, "algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig16_energy_efficiency_vs_reliability.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
    },
    "full": {
        "fig01_pdr_vs_n_snir_off.png": {"mode": {"snir_off"}},
        "fig02_pdr_vs_n_snir_on.png": {"mode": {"snir_on"}},
        "fig03_der_vs_n_snir_off.png": {"mode": {"snir_off"}},
        "fig04_der_vs_n_snir_on.png": {"mode": {"snir_on"}},
        "fig05_throughput_vs_n_snir_off.png": {"mode": {"snir_off"}},
        "fig06_throughput_vs_n_snir_on.png": {"mode": {"snir_on"}},
        "fig07_sf_histogram_by_algo.png": {"mode": {"snir_on"}},
        "fig08_outage_probability_vs_n.png": {"mode": {"snir_on"}},
        "fig09_energy_efficiency_vs_pdr_pareto.png": {},
        "fig10_sinr_cdf_fixed_scenario.png": {"mode": {"snir_on"}},
        "fig11_adaptation_cost_vs_speed.png": {"mode": {"snir_on"}},
        "fig07_tc_vs_speed.png": {"speed": {"1", "3", "5"}},
        "fig08_fairness_vs_n.png": {"mode": {"snir_off", "snir_on"}},
        "fig09_sf_distribution_snir_on.png": {"mode": {"snir_on"}},
        "fig09b_sf_distribution_snir_on_small_multiples.png": {"mode": {"snir_on"}},
        "fig10_sinr_cdf.png": {"mode": {"snir_on"}},
        "fig11_airtime_vs_n.png": {"mode": {"snir_off", "snir_on"}},
        "fig12_switch_count_vs_n.png": {"mode": {"snir_off", "snir_on"}},
        "fig13_ucb_tracking_lag_vs_speed.png": {"algo": {"ucb", "ucb_forget"}, "speed": {"1", "3", "5"}},
        "fig14_pareto_reliability_airtime.png": {},
        "fig15_outage_probability_vs_n.png": {"mode": {"snir_on"}, "speed": {"1", "3", "5"}},
        "fig16_energy_efficiency_vs_reliability.png": {},
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


COLUMN_NAME_ALIASES = {
    "n": "N",
    "algo": "algo",
    "mode": "mode",
    "speed": "speed",
    "sf": "sf",
    "ratio": "ratio",
    "quantile": "quantile",
    "sinr_db": "sinr_db",
    "tc_s": "Tc_s",
    "tc_s_mean": "Tc_s_mean",
    "mobility_model": "mobility_model",
    "model": "mobility_model",
    "gateways": "gateways",
    "sigma": "sigma",
    "sigma_shadowing": "sigma",
}
METRIC_COLUMN_ALIASES = {
    "pdr_mean": ("pdr_mean", "pdr"),
    "der_mean": ("der_mean", "der"),
    "throughput_bps_mean": ("throughput_bps_mean", "throughput_mean_bps", "throughput_bps"),
    "jain_fairness_mean": ("jain_fairness_mean", "jain_fairness"),
    "airtime_total_s_mean": ("airtime_total_s_mean", "airtime_total_s"),
    "switch_count_mean": ("switch_count_mean", "switch_count"),
}

CI95_COLUMN_ALIASES = {
    "pdr_mean": ("pdr_ci95", "pdr_ci95_low", "pdr_ci95_high"),
    "der_mean": ("der_ci95", "der_ci95_low", "der_ci95_high"),
    "throughput_bps_mean": ("throughput_bps_ci95", "throughput_bps_ci95_low", "throughput_bps_ci95_high"),
    "jain_fairness_mean": ("jain_fairness_ci95", "jain_fairness_ci95_low", "jain_fairness_ci95_high"),
    "Tc_s_mean": ("Tc_s_ci95", "Tc_s_ci95_low", "Tc_s_ci95_high"),
    "outage_ratio_mean": ("outage_ratio_ci95", "outage_ratio_ci95_low", "outage_ratio_ci95_high"),
}


@dataclass(frozen=True)
class ScenarioFilters:
    by_column: dict[str, set[str]]

    @classmethod
    def from_tokens(cls, tokens: list[str] | None) -> "ScenarioFilters":
        mapping: dict[str, set[str]] = defaultdict(set)
        for token in tokens or []:
            if "=" not in token:
                warnings.warn(f"Ignored filter (expected format key=value1,value2): {token}", stacklevel=2)
                continue
            key, values = token.split("=", 1)
            key = key.strip()
            if not key:
                warnings.warn(f"Ignored filter (empty key): {token}", stacklevel=2)
                continue
            key = FILTER_COLUMN_ALIASES.get(key, key)
            parsed = [item.strip() for item in values.split(",") if item.strip()]
            if not parsed:
                warnings.warn(f"Ignored filter (no values): {token}", stacklevel=2)
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
    points_by_curve: dict[str, int]
    generated: bool


def _normalize_csv_row(row: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in row.items():
        canonical = COLUMN_NAME_ALIASES.get(str(key).strip().lower(), key)
        normalized[str(canonical)] = value

    if "mode" in normalized:
        normalized["mode"] = _normalize_filter_value("mode", normalized.get("mode", ""))
    if "algo" in normalized:
        normalized["algo"] = _normalize_filter_value("algo", normalized.get("algo", ""))
    if "mobility_model" in normalized:
        mobility_raw = str(normalized.get("mobility_model", "")).strip().lower().replace("-", "_")
        normalized["mobility_model"] = "smooth" if mobility_raw == "smooth" else "rwp"
    return normalized


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        warnings.warn(f"Missing aggregated file: {path}.", stacklevel=2)
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [_normalize_csv_row(row) for row in csv.DictReader(handle)]


def validate_aggregates_inputs(aggregates_dir: Path) -> list[str]:
    """Validate required CSV presence and contractual columns before plotting."""

    errors: list[str] = []
    for key, filename in REQUIRED_FILES.items():
        csv_path = aggregates_dir / filename
        if not csv_path.is_file():
            errors.append(f"missing file: {csv_path}")
            continue
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            raw_fieldnames = reader.fieldnames or []
            normalized_fieldnames = {
                str(COLUMN_NAME_ALIASES.get(str(name).strip().lower(), name)) for name in raw_fieldnames
            }

        expected = REQUIRED_COLUMNS.get(key, set())
        missing: list[str] = []
        for column in sorted(expected):
            candidates = METRIC_COLUMN_ALIASES.get(column, (column,))
            if not any(candidate in normalized_fieldnames for candidate in candidates):
                missing.append(column)

        if missing:
            errors.append(f"missing columns in {csv_path.name}: {', '.join(missing)}")
    return errors


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
    if not (parsed == parsed) or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


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
            f"No rows after filtering. filter={filter_expr}; candidate_rows={len(rows)}. Details: {debug}",
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
            f"{key}∈{sorted(allowed)}: {matched}/{with_key} matching row(s)"
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
    warnings.warn(f"{fig_name} skipped: {reason}", stacklevel=2)


def _algo_series(rows: list[dict[str, str]], *, fig_name: str) -> list[tuple[str, list[dict[str, str]]]]:
    normalized_rows = [_normalize_row_for_filtering(row) for row in rows]
    algos = sorted({row.get("algo", "").strip() for row in normalized_rows if row.get("algo", "").strip()})
    series: list[tuple[str, list[dict[str, str]]]] = []
    for algo in algos:
        algo_rows = [row for row in normalized_rows if row.get("algo", "").strip() == algo]
        if not algo_rows:
            warnings.warn(
                f"{fig_name}: empty series for exact filter algo={algo}. filter=algo={algo}",
                stacklevel=2,
            )
            continue
        series.append((algo, algo_rows))
    return series


def _log_figure_result(path: Path, generated: bool, *, verbose: bool) -> None:
    if not verbose:
        return
    status = "generated" if generated else "skipped"
    print(f"Figure {status}: {path}")

def _is_reliability_metric(y_col: str) -> bool:
    return y_col in {"pdr_mean", "der_mean"}


def _plot_xy_by_algo(
    rows: list[dict[str, str]], *, fig_name: str, y_col: str, out_path: Path, y_scale: str = "auto"
) -> bool:
    resolved_metric = _resolve_metric_column(rows, expected=y_col)
    needed = {"N", "algo", resolved_metric}
    ci95_columns = _resolve_ci95_columns(rows, metric_col=resolved_metric)
    if not rows:
        _warn_skip(fig_name, "no rows available")
        return False
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False

    series = _algo_series(rows, fig_name=fig_name)
    if rows and not series:
        _warn_skip(fig_name, "no series after strict algo filtering")
        return False

    dropped = 0
    y_values: list[float] = []
    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo, algo_rows in series:
        per_x: dict[float, list[float]] = defaultdict(list)
        per_x_csv: dict[float, tuple[float, float, float]] = {}
        for row in algo_rows:
            x = _to_float(row.get("N"))
            y = _to_float(row.get(resolved_metric))
            if x is None or y is None:
                dropped += 1
                continue
            if ci95_columns is not None:
                _, low_col, high_col = ci95_columns
                low = _to_float(row.get(low_col))
                high = _to_float(row.get(high_col))
                if low is not None and high is not None:
                    per_x_csv[x] = (y, low, high)
                    continue
            per_x[x].append(y)
        if not per_x:
            if not per_x_csv:
                warnings.warn(
                    f"{fig_name}: empty algo series after numeric cleanup. filter=algo={algo}",
                    stacklevel=2,
                )
                continue

        xs = sorted(set(per_x) | set(per_x_csv))
        plot_xs: list[float] = []
        means: list[float] = []
        errors: list[float] = []
        lows: list[float] = []
        highs: list[float] = []
        for x in xs:
            if x in per_x_csv:
                mean, low, high = per_x_csv[x]
                plot_xs.append(x)
                means.append(mean)
                errors.append(max(0.0, (high - low) / 2.0))
                lows.append(low)
                highs.append(high)
                y_values.append(mean)
                continue
            ci = ci95_from_samples(per_x[x])
            if ci is None:
                continue
            plot_xs.append(x)
            means.append(ci.mean)
            errors.append(ci.half_width)
            lows.append(ci.mean - ci.half_width)
            highs.append(ci.mean + ci.half_width)
            y_values.append(ci.mean)
        if means:
            style = _algo_style_kwargs(algo)
            plt.plot(plot_xs, means, label=algo, **style)
            plt.fill_between(plot_xs, lows, highs, alpha=0.15, color=style.get("color"))
            plt.errorbar(plot_xs, means, yerr=errors, capsize=3, linestyle="none", color=style.get("color"))
            plotted += 1

    if dropped:
        warnings.warn(f"{fig_name}: {dropped} rows skipped (non-numeric values).", stacklevel=2)
    if plotted == 0:
        _warn_skip(fig_name, "no plottable data after cleanup")
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
                scale_policy = f"auto→zoom [{lower:.3f},{upper:.3f}] + annex [0,1]"
            else:
                plt.ylim(0.0, 1.0)
                scale_policy = "auto→full [0,1]"

    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("N"))
    plt.ylabel(_axis_label(y_col))
    _add_compact_legend(title=f"Algorithm | y-scale: {scale_policy}")
    plt.tight_layout()
    _save_figure_variants(out_path)

    if _is_reliability_metric(y_col) and y_scale == "auto" and y_values and min(y_values) >= 0.9:
        plt.ylim(0.0, 1.0)
        _add_compact_legend(title="Algorithm | y-scale: full annex [0,1]")
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


def _count_points_by_curve(rows: list[dict[str, str]], metric: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    resolved = _resolve_metric_column(rows, expected=metric)

    for row in rows:
        if metric == "sinr_db":
            valid = _to_float(row.get("sinr_db")) is not None and _to_float(row.get("quantile")) is not None
        elif metric == "ratio":
            valid = _to_float(row.get("sf")) is not None and _to_float(row.get("ratio")) is not None
        elif metric == "Tc_s":
            valid = _to_float(row.get("speed")) is not None and _to_float(row.get("Tc_s")) is not None
        else:
            valid = _to_float(row.get("N")) is not None and _to_float(row.get(resolved)) is not None

        if not valid:
            continue

        curve = str(row.get("algo", "all")) if "algo" in row else "all"
        counts[curve] = counts.get(curve, 0) + 1
    return counts


def _resolve_metric_column(rows: list[dict[str, str]], *, expected: str) -> str:
    if not rows:
        return expected
    for candidate in METRIC_COLUMN_ALIASES.get(expected, (expected,)):
        if candidate in rows[0]:
            if candidate != expected:
                warnings.warn(
                    f"Column '{expected}' missing, fallback to '{candidate}' (aggregates compatibility).",
                    stacklevel=3,
                )
            return candidate
    return expected


def _resolve_ci95_columns(rows: list[dict[str, str]], *, metric_col: str) -> tuple[str, str, str] | None:
    if not rows:
        return None
    candidates = CI95_COLUMN_ALIASES.get(metric_col)
    if candidates is None:
        return None
    half, low, high = candidates
    if half in rows[0] and low in rows[0] and high in rows[0]:
        return half, low, high
    return None


def _plot_tc_vs_speed(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "file convergence_tc.csv is empty or missing")
        return False
    tc_column = "Tc_s_mean" if rows and "Tc_s_mean" in rows[0] else "Tc_s"
    needed = {"speed", "algo", tc_column}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False

    series = _algo_series(rows, fig_name=fig_name)
    if not series:
        _warn_skip(fig_name, "no usable speed/Tc_s pairs")
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
            warnings.warn(f"{fig_name}: empty algo series after exact filter. filter=algo={algo}", stacklevel=2)
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
            plt.errorbar(speeds, means, yerr=errors, capsize=3, label=algo, **_algo_style_kwargs(algo))
            plotted += 1
    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "no usable speed/Tc_s pairs")
        return False
    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("speed"))
    plt.ylabel(_axis_label("Tc_s"))
    _add_compact_legend(title="Algorithm")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_sinr_cdf(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "file sinr_cdf.csv is empty or missing")
        return False
    needed = {"algo", "mode", "N", "speed", "mobility_model", "gateways", "sigma", "quantile", "sinr_db"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False

    by_context: dict[tuple[str, str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        context = (
            row.get("mode", ""),
            row.get("N", ""),
            row.get("speed", ""),
            row.get("mobility_model", ""),
            row.get("gateways", ""),
            row.get("sigma", ""),
        )
        by_context[context].append(row)

    ranked = sorted(by_context.items(), key=lambda item: (-len(item[1]), item[0]))
    if not ranked:
        _warn_skip(fig_name, "no scenario context available")
        return False
    chosen_context, chosen_rows = ranked[0]

    grouped: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in chosen_rows:
        q = _to_float(row.get("quantile"))
        sinr = _to_float(row.get("sinr_db"))
        if q is None or sinr is None or q <= 0.0 or q > 1.0:
            continue
        grouped[row.get("algo", "unknown")][q].append(sinr)

    if not grouped:
        _warn_skip(fig_name, "no usable quantile/sinr points")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo in sorted(grouped):
        quantiles = sorted(grouped[algo])
        xs: list[float] = []
        means: list[float] = []
        lows: list[float] = []
        highs: list[float] = []
        for q in quantiles:
            ci = ci95_from_samples(grouped[algo][q])
            if ci is None:
                continue
            xs.append(ci.mean)
            means.append(q)
            lows.append(max(-40.0, ci.mean - ci.half_width))
            highs.append(ci.mean + ci.half_width)
        if not xs:
            continue
        style = _algo_style_kwargs(algo)
        plt.plot(xs, means, label=algo, **style)
        plt.fill_betweenx(means, lows, highs, color=style.get("color"), alpha=0.15)
        plotted += 1

    if plotted == 0:
        _warn_skip(fig_name, "no plottable CDF curve")
        plt.close()
        return False

    mode, n_value, speed, mobility, gateways, sigma = chosen_context
    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("sinr_db"))
    plt.ylabel(_axis_label("quantile"))
    _add_compact_legend(title="Algorithm")
    plt.title(f"Fixed scenario: mode={mode}, N={n_value}, v={speed}, mob={mobility}, gw={gateways}, sigma={sigma}")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True

def _plot_sf_distribution(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "file distribution_sf.csv is empty or missing")
        return False
    needed = {"sf", "algo"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False
    if "ratio" not in rows[0] and "count" not in rows[0]:
        _warn_skip(fig_name, "missing columns ['ratio' or 'count']")
        return False

    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    has_ratio = "ratio" in rows[0]
    for row in rows:
        sf = _to_float(row.get("sf"))
        value = _to_float(row.get("ratio")) if has_ratio else _to_float(row.get("count"))
        if sf is None or value is None:
            continue
        sf_int = int(sf)
        if 7 <= sf_int <= 12:
            grouped[row.get("algo", "unknown")][sf_int].append(value)

    if not grouped:
        _warn_skip(fig_name, "no usable SF/ratio points")
        return False

    sf_values = list(range(7, 13))
    algos = sorted(grouped)
    width = 0.8 / max(len(algos), 1)
    x_positions = list(range(len(sf_values)))

    plt.figure(figsize=(10, 5))
    for idx, algo in enumerate(algos):
        offset = (idx - (len(algos) - 1) / 2) * width
        xs = [x + offset for x in x_positions]
        means_percent: list[float] = []
        ci_percent: list[float] = []
        for sf in sf_values:
            samples = grouped[algo].get(sf, [])
            if has_ratio:
                samples = [sample / 100.0 if sample > 1.5 else sample for sample in samples]
            ci = ci95_from_samples(samples)
            if ci is None:
                means_percent.append(0.0)
                ci_percent.append(0.0)
            else:
                means_percent.append(max(0.0, ci.mean) * 100.0)
                ci_percent.append(max(0.0, ci.half_width) * 100.0)
        style = _algo_style_kwargs(algo)
        plt.bar(xs, means_percent, width=width, label=algo, color=style.get("color"), alpha=0.85)
        plt.errorbar(xs, means_percent, yerr=ci_percent, fmt="none", ecolor=style.get("color"), capsize=2)

    plt.grid(axis="y", alpha=0.3)
    plt.xlabel(_axis_label("sf"))
    plt.ylabel("Usage share (%)")
    plt.xticks(x_positions, [str(sf) for sf in sf_values])
    _add_compact_legend(title="Algorithm")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True

def _plot_sf_distribution_small_multiples(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "file distribution_sf.csv is empty or missing")
        return False
    needed = {"sf", "algo"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False
    if "ratio" not in rows[0] and "count" not in rows[0]:
        _warn_skip(fig_name, "missing columns ['ratio' or 'count']")
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
        _warn_skip(fig_name, "no usable SF/ratio points")
        return False

    sf_values = list(range(7, 13))
    algos = sorted(grouped)
    # Unified output format: always render usage share as percentages (0-100%).
    data_percent: dict[str, list[float]] = {}
    for algo in algos:
        means = {sf: sum(grouped[algo][sf]) / len(grouped[algo][sf]) for sf in grouped[algo]}
        ordered = [max(0.0, means.get(sf, 0.0)) for sf in sf_values]
        if has_ratio:
            total = sum(ordered)
            if total > 1.5:
                ordered = [value / 100.0 for value in ordered]
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
        axis.bar(x_positions, data_percent[algo], width=0.7, label=algo, color=_algo_style_kwargs(algo).get("color"))
        axis.grid(axis="y", alpha=0.3)
        axis.set_ylim(0, 100)
        axis.set_yticks(y_ticks)
        axis.legend(loc="upper right", title="Algorithm", fontsize=8, title_fontsize=9, frameon=False)

    axes_list[-1].set_xticks(x_positions, [str(sf) for sf in sf_values])
    axes_list[-1].set_xlabel(_axis_label("sf"))
    fig.supylabel("Usage share (%)")
    fig.tight_layout()
    fig.savefig(out_path.with_suffix(".png"), dpi=PLOT_DPI)
    fig.savefig(out_path.with_suffix(".pdf"))
    plt.close(fig)
    return True


def _plot_delta_pdr_on_minus_off(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "no rows available")
        return False
    pdr_col = _resolve_metric_column(rows, expected="pdr_mean")
    needed = {"N", "algo", "mode", pdr_col}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
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
        _warn_skip(fig_name, "no usable N/algo pair")
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
            plt.errorbar(xs, means, yerr=errors, capsize=3, label=algo, **_algo_style_kwargs(algo))

    if not plt.gca().lines:
        plt.close()
        _warn_skip(fig_name, "no aligned SNIR_ON/SNIR_OFF pair")
        return False

    plt.axhline(0.0, color="black", linewidth=1.0, linestyle="--", alpha=0.6)
    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("N"))
    plt.ylabel("ΔPDR (SNIR_ON - SNIR_OFF)")
    _add_compact_legend(title="Algorithm")
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
        _warn_skip(fig_name, "no rows available")
        return False
    switch_col = _resolve_metric_column(rows, expected="switch_count_mean")
    needed = {"speed", "algo", switch_col}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False

    grouped: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        speed = _to_float(row.get("speed"))
        switch_count = _to_float(row.get(switch_col))
        if speed is None or switch_count is None:
            continue
        grouped[row.get("algo", "unknown")][speed].append(switch_count / _duration_hours_from_row(row))

    if not grouped:
        _warn_skip(fig_name, "no usable speed/switch_count pairs")
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
        plt.errorbar(speeds, means, yerr=errors, capsize=3, label=algo, **_algo_style_kwargs(algo))

    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("speed"))
    plt.ylabel("Instability (switch_count/h)")
    _add_compact_legend(title="Algorithm")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True




def _plot_ucb_tracking_lag_vs_speed(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "file ucb_tracking.csv is empty or missing")
        return False
    tc_column = "Tc_s_mean" if rows and "Tc_s_mean" in rows[0] else "Tc_s"
    needed = {"speed", "algo", tc_column}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False

    series = _algo_series(rows, fig_name=fig_name)
    if not series:
        _warn_skip(fig_name, "no usable speed/Tc_s pairs")
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
            warnings.warn(f"{fig_name}: empty algo series after exact filter. filter=algo={algo}", stacklevel=2)
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
            plt.errorbar(speeds, means, yerr=errors, capsize=3, label=algo, **_algo_style_kwargs(algo))
            plotted += 1
    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "no usable speed/Tc_s pairs")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("speed"))
    plt.ylabel(_axis_label("Tc_s"))
    _add_compact_legend(title="Algorithm")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_outage_probability_vs_n(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "file outage_probability.csv is empty or missing")
        return False
    needed = {"algo", "N", "outage_prob_mean", "outage_prob_ci95"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False

    grouped: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    for row in rows:
        n_value = _to_float(row.get("N"))
        outage = _to_float(row.get("outage_prob_mean"))
        ci95 = _to_float(row.get("outage_prob_ci95"))
        if n_value is None or outage is None:
            continue
        grouped[row.get("algo", "unknown")].append((n_value, outage, ci95 or 0.0))

    if not grouped:
        _warn_skip(fig_name, "no usable outage/N point")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
    for algo in sorted(grouped):
        points = sorted(grouped[algo], key=lambda item: item[0])
        xs = [item[0] for item in points]
        ys = [item[1] for item in points]
        errs = [item[2] for item in points]
        if not xs:
            continue
        plt.errorbar(xs, ys, yerr=errs, capsize=3, label=algo, **_algo_style_kwargs(algo))
        plotted += 1

    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "no plottable outage vs N series")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("N"))
    plt.ylabel("Outage probability")
    plt.ylim(0, 1)
    _add_compact_legend(title="Algorithm")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_energy_efficiency_vs_reliability(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "file energy_efficiency_reliability.csv is empty or missing")
        return False
    needed = {"algo", "pdr_mean", "pdr_ci95", "energy_efficiency_mean", "energy_efficiency_ci95"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False

    grouped: dict[str, list[tuple[float, float, float, float]]] = defaultdict(list)
    for row in rows:
        pdr_mean = _to_float(row.get("pdr_mean"))
        pdr_ci95 = _to_float(row.get("pdr_ci95")) or 0.0
        eff_mean = _to_float(row.get("energy_efficiency_mean"))
        eff_ci95 = _to_float(row.get("energy_efficiency_ci95")) or 0.0
        if pdr_mean is None or eff_mean is None:
            continue
        grouped[row.get("algo", "unknown")].append((pdr_mean, pdr_ci95, eff_mean, eff_ci95))

    if not grouped:
        _warn_skip(fig_name, "no usable efficiency/PDR pairs")
        return False

    plt.figure(figsize=(8, 5))
    ax = plt.gca()
    plotted = 0
    for algo in sorted(grouped):
        style = _algo_style_kwargs(algo)
        xs = [v[0] for v in grouped[algo]]
        ys = [v[2] for v in grouped[algo]]
        ci_x = ci95_from_samples(xs)
        ci_y = ci95_from_samples(ys)
        if ci_x is None or ci_y is None:
            continue
        ax.errorbar([ci_x.mean], [ci_y.mean], xerr=[ci_x.half_width], yerr=[ci_y.half_width], markersize=7, capsize=4, label=algo, **style)
        ax.scatter([ci_x.mean], [ci_y.mean], color=style.get("color"), marker=style.get("marker"), s=45)
        plotted += 1

    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "no plottable mean±CI95 point")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("pdr_mean"))
    plt.ylabel("Energy efficiency (throughput/airtime)")
    plt.xlim(0, 1.05)
    _add_compact_legend(title="Pareto frontier")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True

def _plot_airtime_reliability_pareto(rows: list[dict[str, str]], out_path: Path) -> bool:
    """Compromis PDR vs airtime avec point moyen et ellipse IC95 par algorithme."""

    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "file pareto_reliability_airtime.csv is empty or missing")
        return False
    needed = {"algo", "pdr_mean", "pdr_ci95", "airtime_total_s_mean", "airtime_total_s_ci95"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"missing columns {missing}")
        return False

    grouped: dict[str, list[tuple[float, float, float, float]]] = defaultdict(list)
    for row in rows:
        pdr_mean = _to_float(row.get("pdr_mean"))
        pdr_ci95 = _to_float(row.get("pdr_ci95")) or 0.0
        airtime_mean = _to_float(row.get("airtime_total_s_mean"))
        airtime_ci95 = _to_float(row.get("airtime_total_s_ci95")) or 0.0
        if pdr_mean is None or airtime_mean is None:
            continue
        grouped[row.get("algo", "unknown")].append((airtime_mean, airtime_ci95, pdr_mean, pdr_ci95))

    if not grouped:
        _warn_skip(fig_name, "no usable airtime/PDR pairs")
        return False

    plt.figure(figsize=(8, 5))
    ax = plt.gca()
    plotted = 0
    for algo in sorted(grouped):
        xs = [v[0] for v in grouped[algo]]
        ys = [v[2] for v in grouped[algo]]
        ci_x = ci95_from_samples(xs)
        ci_y = ci95_from_samples(ys)
        if ci_x is None or ci_y is None:
            continue
        ax.scatter([ci_x.mean], [ci_y.mean], s=45, label=algo, color=_algo_style_kwargs(algo).get("color"), marker=_algo_style_kwargs(algo).get("marker"))
        ax.add_patch(Ellipse((ci_x.mean, ci_y.mean), width=max(2.0 * ci_x.half_width, 1e-12), height=max(2.0 * ci_y.half_width, 1e-12), fill=False, alpha=0.65, edgecolor=_algo_style_kwargs(algo).get("color")))
        plotted += 1

    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "no plottable mean±CI95 point")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("airtime_total_s_mean"))
    plt.ylabel(_axis_label("pdr_mean"))
    plt.ylim(0, 1.05)
    _add_compact_legend(title="Algorithm")
    plt.tight_layout()
    _save_figure_variants(out_path)
    plt.close()
    return True


def _plot_adaptation_cost_vs_speed(
    metric_rows: list[dict[str, str]],
    tc_rows: list[dict[str, str]],
    out_path: Path,
) -> bool:
    fig_name = out_path.name
    if not metric_rows or not tc_rows:
        _warn_skip(fig_name, "metric_by_factor.csv or convergence_tc.csv is empty or missing")
        return False

    switch_col = _resolve_metric_column(metric_rows, expected="switch_count_mean")
    tc_column = "Tc_s_mean" if tc_rows and "Tc_s_mean" in tc_rows[0] else "Tc_s"

    switch_by_key: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in metric_rows:
        algo = row.get("algo", "unknown")
        speed = row.get("speed", "")
        mode = row.get("mode", "")
        speed_value = _to_float(speed)
        switch_count = _to_float(row.get(switch_col))
        if speed_value is None or switch_count is None:
            continue
        switch_by_key[(algo, str(speed_value), mode)].append(switch_count)

    tc_by_key: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in tc_rows:
        algo = row.get("algo", "unknown")
        speed = row.get("speed", "")
        mode = row.get("mode", "")
        speed_value = _to_float(speed)
        tc = _to_float(row.get(tc_column))
        if speed_value is None or tc is None:
            continue
        tc_by_key[(algo, str(speed_value), mode)].append(tc)

    grouped: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for key, switch_samples in switch_by_key.items():
        if key not in tc_by_key:
            continue
        algo, speed_token, _ = key
        speed_value = _to_float(speed_token)
        if speed_value is None:
            continue
        ci_switch = ci95_from_samples(switch_samples)
        ci_tc = ci95_from_samples(tc_by_key[key])
        if ci_switch is None or ci_tc is None:
            continue
        grouped[algo][speed_value].append(ci_switch.mean + ci_tc.mean)

    if not grouped:
        _warn_skip(fig_name, "no aligned speed/switch_count/Tc pairs")
        return False

    plt.figure(figsize=(8, 5))
    plotted = 0
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
        if means:
            plt.errorbar(speeds, means, yerr=errors, capsize=3, label=algo, **_algo_style_kwargs(algo))
            plotted += 1

    if plotted == 0:
        plt.close()
        _warn_skip(fig_name, "no plottable adaptation cost curve")
        return False

    plt.grid(alpha=0.3)
    plt.xlabel(_axis_label("speed"))
    plt.ylabel(_axis_label("adaptation_cost"))
    _add_compact_legend(title="Algorithm")
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
        raise ValueError(f"Unknown article profile: {article_profile}")

    random.seed(42)
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
                points_by_curve=_count_points_by_curve(selected, metric),
                generated=did_generate,
            )
        )
        _log_figure_result(out_path, did_generate, verbose=verbose)
        if did_generate:
            generated.append(out_path)

    sf_name = "fig07_sf_histogram_by_algo.png"
    sf_filters = filters.merge(_resolve_profile_filter(article_profile, sf_name))
    sf_selected = _apply_filters(payloads["distribution_sf"], sf_filters)
    sf_path = out_dir / _stable_figure_name(sf_name)
    did_generate = _plot_sf_distribution(sf_selected, sf_path)
    traces.append(
        FigureTrace(
            figure=sf_path.name,
            source="distribution_sf",
            metric="ratio",
            filters=_filters_to_serializable(sf_filters),
            num_points=_count_points(sf_selected, "ratio"),
            points_by_curve=_count_points_by_curve(sf_selected, "ratio"),
            generated=did_generate,
        )
    )
    _log_figure_result(sf_path, did_generate, verbose=verbose)
    if did_generate:
        generated.append(sf_path)

    if include_bonus:
        for fig_name, source, metric, local_filter in CONTRIBUTION_SPECS:
            effective_filters = filters.merge(local_filter).merge(_resolve_profile_filter(article_profile, fig_name))
            selected = _apply_filters(payloads[source], effective_filters)
            out_path = out_dir / _stable_figure_name(fig_name)
            if fig_name == "fig08_outage_probability_vs_n.png":
                did_generate = _plot_outage_probability_vs_n(selected, out_path)
            elif fig_name == "fig09_energy_efficiency_vs_pdr_pareto.png":
                did_generate = _plot_energy_efficiency_vs_reliability(selected, out_path)
            elif fig_name == "fig10_sinr_cdf_fixed_scenario.png":
                did_generate = _plot_sinr_cdf(selected, out_path)
            elif fig_name == "fig11_adaptation_cost_vs_speed.png":
                tc_selected = _apply_filters(payloads["convergence_tc"], effective_filters)
                did_generate = _plot_adaptation_cost_vs_speed(selected, tc_selected, out_path)
            else:
                did_generate = _plot_xy_by_algo(selected, fig_name=fig_name, y_col=metric, out_path=out_path, y_scale=y_scale)
            traces.append(
                FigureTrace(
                    figure=out_path.name,
                    source=source,
                    metric=metric,
                    filters=_filters_to_serializable(effective_filters),
                    num_points=_count_points(selected, metric),
                    points_by_curve=_count_points_by_curve(selected, metric),
                    generated=did_generate,
                )
            )
            _log_figure_result(out_path, did_generate, verbose=verbose)
            if did_generate:
                generated.append(out_path)

    manifest_path = out_dir / "plots_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["figure", "source", "filter", "date", "nb_points"])
        writer.writeheader()
        for trace in traces:
            writer.writerow(
                {
                    "figure": trace.figure,
                    "source": REQUIRED_FILES.get(trace.source, trace.source),
                    "filter": json.dumps(trace.filters, ensure_ascii=False, sort_keys=True),
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
                "points_by_curve": trace.points_by_curve,
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
    parser = argparse.ArgumentParser(description="Generate core and contribution figures from aggregates/*.csv")
    parser.add_argument("--aggregates-dir", required=True, type=Path, help="Directory containing aggregated CSV files.")
    parser.add_argument("--out", required=True, type=Path, help="Target directory for PNG files.")
    parser.add_argument(
        "--scenario-filter",
        action="append",
        default=[],
        help="Filter key=val1,val2 (repeatable), e.g.: --scenario-filter mode=snir_on --scenario-filter algo=ucb,legacy",
    )
    parser.add_argument("--no-bonus", action="store_true", help="Do not generate contribution figures fig08..fig11.")
    parser.add_argument("--ieee-ready", action="store_true", help="Enable IEEE style (colorblind-friendly palette, linewidths, PDF+PNG export).")
    parser.add_argument(
        "--article-profile",
        choices=sorted(ARTICLE_PROFILE_FILTERS),
        default="core",
        help="Fixed article profile to enforce documented per-figure filters (core or full).",
    )
    parser.add_argument(
        "--y-scale",
        choices=["auto", "full", "zoom"],
        default="auto",
        help="Y-axis policy for PDR/DER: auto (zoom near 1 + full-scale annex), full ([0,1]), zoom.",
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
    print(f"{len(generated)} figure(s) generated(s).")
    for path in generated:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

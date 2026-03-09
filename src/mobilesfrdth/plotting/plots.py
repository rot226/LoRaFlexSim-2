"""Génération des figures à partir de ``aggregates/*.csv`` uniquement."""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REQUIRED_FILES = {
    "metric_by_factor": "metric_by_factor.csv",
    "distribution_sf": "distribution_sf.csv",
    "convergence_tc": "convergence_tc.csv",
    "sinr_cdf": "sinr_cdf.csv",
    "fairness_airtime_switching": "fairness_airtime_switching.csv",
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
    "sinr_cdf": {"algo", "mode", "N", "quantile", "sinr_db"},
    "fairness_airtime_switching": {"N", "algo", "jain_fairness", "airtime_total_s", "switch_count"},
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
        "fig09_sf_distribution.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig10_sinr_cdf.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig11_airtime_vs_n.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
        "fig12_switch_count_vs_n.png": {"algo": {"adr", "adr_mixra", "ucb", "ucb_forget"}},
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
        "fig09_sf_distribution.png": {"mode": {"snir_off", "snir_on"}},
        "fig10_sinr_cdf.png": {"mode": {"snir_on"}},
        "fig11_airtime_vs_n.png": {"mode": {"snir_off", "snir_on"}},
        "fig12_switch_count_vs_n.png": {"mode": {"snir_off", "snir_on"}},
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


def _log_figure_result(path: Path, generated: bool, *, verbose: bool) -> None:
    if not verbose:
        return
    status = "générée" if generated else "ignorée"
    print(f"Figure {status}: {path}")

def _plot_xy_by_algo(rows: list[dict[str, str]], *, fig_name: str, y_col: str, out_path: Path) -> bool:
    resolved_metric = _resolve_metric_column(rows, expected=y_col)
    needed = {"N", "algo", resolved_metric}
    if not rows:
        _warn_skip(fig_name, "aucune ligne disponible")
        return False
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    clean_rows: list[dict[str, str]] = []
    dropped = 0
    for row in rows:
        x = _to_float(row.get("N"))
        y = _to_float(row.get(resolved_metric))
        if x is None or y is None:
            dropped += 1
            continue
        normalized = dict(row)
        normalized["_x"] = str(x)
        normalized["_y"] = str(y)
        clean_rows.append(normalized)

    if dropped:
        warnings.warn(f"{fig_name}: {dropped} lignes ignorées (valeurs non numériques).", stacklevel=2)

    algos = sorted({row.get("algo", "unknown") for row in clean_rows})
    if not algos:
        _warn_skip(fig_name, "aucune donnée traçable après nettoyage")
        return False

    plt.figure(figsize=(8, 5))
    for algo in algos:
        algo_rows = [row for row in clean_rows if row.get("algo", "unknown") == algo]
        points = sorted(
            ((float(row["_x"]), float(row["_y"])) for row in algo_rows),
            key=lambda item: item[0],
        )
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        plt.plot(xs, ys, marker="o", label=algo)
    plt.grid(alpha=0.3)
    plt.xlabel("N")
    plt.ylabel(y_col)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return True


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
    needed = {"speed", "algo", "Tc_s"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    grouped: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        speed = _to_float(row.get("speed"))
        tc_s = _to_float(row.get("Tc_s"))
        if speed is None or tc_s is None:
            continue
        grouped[row.get("algo", "unknown")][speed].append(tc_s)

    if not grouped:
        _warn_skip(fig_name, "pas de couples speed/Tc_s exploitables")
        return False

    plt.figure(figsize=(8, 5))
    for algo in sorted(grouped):
        speeds = sorted(grouped[algo])
        means = [sum(grouped[algo][speed]) / len(grouped[algo][speed]) for speed in speeds]
        plt.plot(speeds, means, marker="o", label=algo)
    plt.grid(alpha=0.3)
    plt.xlabel("speed")
    plt.ylabel("Tc_s moyen")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return True


def _plot_sinr_cdf(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "fichier sinr_cdf.csv vide ou absent")
        return False
    needed = {"algo", "mode", "N", "quantile", "sinr_db"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    by_group: dict[tuple[str, str, str], list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        q = _to_float(row.get("quantile"))
        sinr = _to_float(row.get("sinr_db"))
        if q is None or sinr is None:
            continue
        algo = row.get("algo", "unknown")
        mode = row.get("mode", "")
        n = row.get("N", "")
        by_group[(algo, mode, n)].append((q, sinr))

    if not by_group:
        _warn_skip(fig_name, "pas de points quantile/sinr exploitables")
        return False

    aggregated: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (algo, mode, n), points in sorted(by_group.items()):
        points.sort(key=lambda item: item[0])
        quantiles = [item[0] for item in points]
        if any(q < 0.0 or q > 1.0 for q in quantiles):
            _warn_skip(fig_name, f"quantile hors [0..1] pour groupe algo={algo}, mode={mode}, N={n}")
            return False
        if any(curr < prev for prev, curr in zip(quantiles, quantiles[1:], strict=False)):
            _warn_skip(fig_name, f"quantile non monotone croissant pour groupe algo={algo}, mode={mode}, N={n}")
            return False

        for q, sinr in points:
            aggregated[algo][q].append(sinr)

    plt.figure(figsize=(8, 5))
    for algo in sorted(aggregated):
        quantiles = sorted(aggregated[algo])
        sinrs = [sum(aggregated[algo][q]) / len(aggregated[algo][q]) for q in quantiles]
        plt.plot(sinrs, quantiles, label=algo)
    plt.grid(alpha=0.3)
    plt.xlabel("SINR (dB)")
    plt.ylabel("Probabilité cumulée")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return True


def _plot_sf_distribution(rows: list[dict[str, str]], out_path: Path) -> bool:
    fig_name = out_path.name
    if not rows:
        _warn_skip(fig_name, "fichier distribution_sf.csv vide ou absent")
        return False
    needed = {"sf", "ratio", "algo"}
    missing = [column for column in needed if column not in rows[0]]
    if missing:
        _warn_skip(fig_name, f"colonnes manquantes {missing}")
        return False

    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        sf = _to_float(row.get("sf"))
        ratio = _to_float(row.get("ratio"))
        if sf is None or ratio is None:
            continue
        grouped[row.get("algo", "unknown")][int(sf)].append(ratio)

    if not grouped:
        _warn_skip(fig_name, "pas de points SF/ratio exploitables")
        return False

    plt.figure(figsize=(8, 5))
    for algo in sorted(grouped):
        sfs = sorted(grouped[algo])
        means = [sum(grouped[algo][sf]) / len(grouped[algo][sf]) for sf in sfs]
        plt.plot(sfs, means, marker="o", label=algo)
    plt.grid(alpha=0.3)
    plt.xlabel("Spreading Factor")
    plt.ylabel("Ratio moyen")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
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
) -> tuple[list[Path], list[FigureTrace]]:
    if article_profile not in ARTICLE_PROFILE_FILTERS:
        raise ValueError(f"Profil article inconnu: {article_profile}")

    out_dir.mkdir(parents=True, exist_ok=True)
    payloads = {name: _read_csv_rows(aggregates_dir / filename) for name, filename in REQUIRED_FILES.items()}

    generated: list[Path] = []
    traces: list[FigureTrace] = []

    for fig_name, source, metric, local_filter in FIGURE_SPECS:
        effective_filters = filters.merge(local_filter).merge(_resolve_profile_filter(article_profile, fig_name))
        selected = _apply_filters(payloads[source], effective_filters)
        out_path = out_dir / fig_name
        did_generate = _plot_xy_by_algo(selected, fig_name=fig_name, y_col=metric, out_path=out_path)
        traces.append(
            FigureTrace(
                figure=fig_name,
                source=source,
                metric=metric,
                filters=_filters_to_serializable(effective_filters),
                generated=did_generate,
            )
        )
        _log_figure_result(out_path, did_generate, verbose=verbose)
        if did_generate:
            generated.append(out_path)

    fig07 = out_dir / "fig07_tc_vs_speed.png"
    fig07_filters = filters.merge(_resolve_profile_filter(article_profile, fig07.name))
    did_generate = _plot_tc_vs_speed(_apply_filters(payloads["convergence_tc"], fig07_filters), fig07)
    traces.append(
        FigureTrace(
            figure=fig07.name,
            source="convergence_tc",
            metric="Tc_s",
            filters=_filters_to_serializable(fig07_filters),
            generated=did_generate,
        )
    )
    _log_figure_result(fig07, did_generate, verbose=verbose)
    if did_generate:
        generated.append(fig07)

    fig08 = out_dir / "fig08_fairness_vs_n.png"
    fig08_filters = filters.merge(_resolve_profile_filter(article_profile, fig08.name))
    did_generate = _plot_xy_by_algo(
        _apply_filters(payloads["metric_by_factor"], fig08_filters),
        fig_name=fig08.name,
        y_col="jain_fairness_mean",
        out_path=fig08,
    )
    traces.append(
        FigureTrace(
            figure=fig08.name,
            source="metric_by_factor",
            metric="jain_fairness_mean",
            filters=_filters_to_serializable(fig08_filters),
            generated=did_generate,
        )
    )
    _log_figure_result(fig08, did_generate, verbose=verbose)
    if did_generate:
        generated.append(fig08)

    fig09 = out_dir / "fig09_sf_distribution.png"
    fig09_filters = filters.merge(_resolve_profile_filter(article_profile, fig09.name))
    did_generate = _plot_sf_distribution(_apply_filters(payloads["distribution_sf"], fig09_filters), fig09)
    traces.append(
        FigureTrace(
            figure=fig09.name,
            source="distribution_sf",
            metric="ratio",
            filters=_filters_to_serializable(fig09_filters),
            generated=did_generate,
        )
    )
    _log_figure_result(fig09, did_generate, verbose=verbose)
    if did_generate:
        generated.append(fig09)

    fig10 = out_dir / "fig10_sinr_cdf.png"
    fig10_filters = filters.merge(_resolve_profile_filter(article_profile, fig10.name))
    did_generate = _plot_sinr_cdf(_apply_filters(payloads["sinr_cdf"], fig10_filters), fig10)
    traces.append(
        FigureTrace(
            figure=fig10.name,
            source="sinr_cdf",
            metric="sinr_db",
            filters=_filters_to_serializable(fig10_filters),
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
            out_path = out_dir / fig_name
            did_generate = _plot_xy_by_algo(selected, fig_name=fig_name, y_col=metric, out_path=out_path)
            traces.append(
                FigureTrace(
                    figure=fig_name,
                    source=source,
                    metric=metric,
                    filters=_filters_to_serializable(effective_filters),
                    generated=did_generate,
                )
            )
            _log_figure_result(out_path, did_generate, verbose=verbose)
            if did_generate:
                generated.append(out_path)

    summary_payload = {
        "article_profile": article_profile,
        "requested_filters": _filters_to_serializable(filters),
        "figures": [
            {
                "figure": trace.figure,
                "source": trace.source,
                "metric": trace.metric,
                "filters": trace.filters,
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
    parser = argparse.ArgumentParser(description="Génère les figures fig01..fig10 (et bonus fig11..fig12) depuis aggregates/*.csv")
    parser.add_argument("--aggregates-dir", required=True, type=Path, help="Répertoire contenant les CSV agrégés.")
    parser.add_argument("--out", required=True, type=Path, help="Répertoire cible pour les PNG.")
    parser.add_argument(
        "--scenario-filter",
        action="append",
        default=[],
        help="Filtre clé=val1,val2 (répétable), ex: --scenario-filter mode=snir_on --scenario-filter algo=ucb,legacy",
    )
    parser.add_argument("--no-bonus", action="store_true", help="N'écrit pas les figures bonus fig11/fig12.")
    parser.add_argument(
        "--article-profile",
        choices=sorted(ARTICLE_PROFILE_FILTERS),
        default="core",
        help="Profil d'article figé pour imposer les filtres documentés par figure (core ou full).",
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
    )
    print(f"{len(generated)} figure(s) générée(s).")
    for path in generated:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

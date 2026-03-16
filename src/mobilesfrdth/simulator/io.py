"""Entrées/sorties CSV pour runs et agrégations mobilesfrdth."""

from __future__ import annotations

import csv
import json
import math
import warnings
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from statistics import stdev

from .metrics import convergence_tc, der, jain_fairness, outage_ratio, pdr, throughput
from ..scenarios import RECOMMENDED_TIME_BIN_S, validate_time_bin_s


TC_PROTOCOL_DT_S = RECOMMENDED_TIME_BIN_S
TC_PROTOCOL_TOLERANCE = 0.1
TC_PROTOCOL_STABLE_BINS = 5
DEFAULT_SINR_CDF_QUANTILE_STEP = 0.05
STUDENT_T_975_BY_DF: dict[int, float] = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}

SCENARIO_ID_COLUMNS = ["N", "speed", "mobility_model", "mode", "algo", "gateways", "sigma_shadowing", "seed", "rep"]
EVENT_COLUMNS = [
    *SCENARIO_ID_COLUMNS,
    "run_id",
    "event_idx",
    "time_s",
    "event_type",
    "node_id",
    "sf",
    "snr_db",
    "sinr_db",
    "threshold_db",
    "success",
    "delivered",
    "payload_bytes",
    "airtime_s",
    "outage",
    "switch_count",
    "regret_proxy",
    "exploration_rate",
    "decision_stability",
    "decision_reason",
    "target_sf",
    "generated_packets_total",
    "dropped_packets_total",
    "buffer_occupancy",
    "retry_attempt",
]
NODE_TIMESERIES_COLUMNS = [
    *SCENARIO_ID_COLUMNS,
    "run_id",
    "bin_start_s",
    "bin_end_s",
    "node_id",
    "tx_count",
    "success_count",
    "delivery_ratio",
    "throughput_bps",
    "mean_snr_db",
    "mean_sinr_db",
    "airtime_s",
    "outage_count",
    "switch_count",
    "regret_proxy_mean",
    "exploration_rate_mean",
    "decision_stability_mean",
]
SUMMARY_COLUMNS = [
    *SCENARIO_ID_COLUMNS,
    "run_id",
    "duration_s",
    "node_count",
    "tx_count",
    "success_count",
    "generated_packets",
    "delivered_bytes",
    "pdr",
    "der",
    "throughput_bps",
    "Tc_s",
    "tc_method",
    "tc_dt_s",
    "jain_fairness",
    "airtime_total_s",
    "airtime_mean_per_node_s",
    "outage_ratio",
    "switch_count",
]


def _scenario_row(run_config: Mapping[str, Any]) -> dict[str, Any]:
    row = {key: run_config.get(key, "") for key in SCENARIO_ID_COLUMNS}
    if row.get("sigma_shadowing", "") == "":
        row["sigma_shadowing"] = run_config.get("sigma", "")
    return row


def _coerce_event(event: Any) -> dict[str, Any]:
    if isinstance(event, Mapping):
        return dict(event)
    payload: dict[str, Any] = {
        "time_s": getattr(event, "time_s", 0.0),
        "event_type": getattr(event, "kind", "uplink"),
        "node_id": getattr(event, "node_id", -1),
    }
    for field in (
        "sf",
        "snr_db",
        "sinr_db",
        "threshold_db",
        "success",
        "delivered",
        "payload_bytes",
        "airtime_s",
        "outage",
        "switch_count",
        "decision_reason",
        "target_sf",
        "generated_packets_total",
        "dropped_packets_total",
        "buffer_occupancy",
        "retry_attempt",
    ):
        if hasattr(event, field):
            payload[field] = getattr(event, field)
    return payload


def _write_csv(path: Path, columns: list[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _ci95_critical_value(n: int) -> float:
    if n <= 1:
        return 0.0
    if n <= 30:
        return STUDENT_T_975_BY_DF[n - 1]
    return 1.96


def _mean_std_ci95_stats(values: list[float], *, allow_inf: bool = False) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "std": 0.0, "n": 0.0, "ci95": 0.0, "ci95_low": 0.0, "ci95_high": 0.0}
    if allow_inf:
        finite_values = [value for value in values if math.isfinite(value)]
        if not finite_values:
            return {"mean": math.inf, "std": 0.0, "n": 0.0, "ci95": 0.0, "ci95_low": math.inf, "ci95_high": math.inf}
        values = finite_values

    mean = sum(values) / len(values)
    n = float(len(values))
    if len(values) < 2:
        return {"mean": mean, "std": 0.0, "n": n, "ci95": 0.0, "ci95_low": mean, "ci95_high": mean}

    std = stdev(values)
    half_width = _ci95_critical_value(len(values)) * std / math.sqrt(len(values))
    return {
        "mean": mean,
        "std": std,
        "n": n,
        "ci95": half_width,
        "ci95_low": mean - half_width,
        "ci95_high": mean + half_width,
    }


def write_run_outputs(
    *,
    output_root: Path,
    run_id: str,
    run_config: Mapping[str, Any],
    events: Iterable[Any],
    duration_s: float,
    time_bin_s: float = 10.0,
) -> dict[str, Path]:
    """Écrit les artefacts d'un run dans ``results/<run_id>/``.

    Protocole de référence pour le calcul de ``Tc_s`` (convergence) :
    - ``dt_s = 10`` secondes comme référence protocolaire
    - ``tolerance = 0.1`` (seuil à ``1 - tolerance = 0.9`` du régime stationnaire)
    - ``stable_bins = 5`` bins de fin de série pour estimer le régime stationnaire

    ``Tc_s`` est évalué via :func:`mobilesfrdth.simulator.metrics.convergence_tc`
    sur une série temporelle de performance (``PDR`` par bin). Si la convergence
    n'est pas observée, la valeur est ``inf``.

    Contrat de métriques:
    - ``switch_count`` (summary + séries temporelles) compte les transitions SF
      effectives, i.e. l'agrégation somme uniquement les incréments de compteur
      entre deux uplinks d'un même nœud (pas la valeur cumulée brute de l'événement).
    - ``jain_fairness`` est calculé explicitement sur la distribution des succès
      par nœud du run (et non sur l'airtime ni sur une moyenne implicite).
    """

    if duration_s <= 0:
        raise ValueError("duration_s doit être > 0")
    time_bin_s = validate_time_bin_s(time_bin_s, field_name="time_bin_s")
    tc_method = "protocol_dt"
    tc_dt_s = TC_PROTOCOL_DT_S
    if not math.isclose(time_bin_s, TC_PROTOCOL_DT_S, rel_tol=0.0, abs_tol=1e-9):
        tc_method = "native_dt"
        tc_dt_s = time_bin_s
        warnings.warn(
            (
                f"Run {run_id}: time_bin_s={time_bin_s:.6g}s diffère du protocole Tc "
                f"({TC_PROTOCOL_DT_S:.1f}s). Tc sera calculé avec le pas natif (tc_dt_s={tc_dt_s:.6g}s)."
            ),
            RuntimeWarning,
            stacklevel=2,
        )

    run_dir = output_root / "results" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    run_config_path = run_dir / "run_config.json"
    run_config_path.write_text(json.dumps(dict(run_config), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    scenario = _scenario_row(run_config)
    event_rows: list[dict[str, Any]] = []
    bins: dict[tuple[int, int], dict[str, Any]] = {}
    node_successes: Counter[int] = Counter()
    node_airtime: Counter[int] = Counter()

    tx_count = 0
    success_count = 0
    generated_packets = 0
    delivered_bytes = 0
    outage_events = 0
    total_switch_count = 0
    node_previous_switch_count: dict[int, int] = defaultdict(int)
    node_generated_totals: dict[int, int] = defaultdict(int)

    anomaly_count = 0

    for idx, item in enumerate(events):
        event = _coerce_event(item)

        required_fields = ("event_type", "time_s", "node_id")
        missing_required = [field for field in required_fields if field not in event]
        if missing_required:
            anomaly_count += 1
            warnings.warn(
                (
                    f"Événement invalide ignoré à l'index {idx}: "
                    f"champ(s) obligatoire(s) manquant(s): {', '.join(sorted(missing_required))}"
                ),
                RuntimeWarning,
                stacklevel=2,
            )
            continue

        event_type = str(event["event_type"])
        if event_type == "uplink":
            uplink_missing = [field for field in ("success", "delivered") if field not in event]
            if uplink_missing:
                anomaly_count += 1
                warnings.warn(
                    (
                        f"Événement uplink invalide ignoré à l'index {idx}: "
                        f"champ(s) obligatoire(s) manquant(s): {', '.join(sorted(uplink_missing))}"
                    ),
                    RuntimeWarning,
                    stacklevel=2,
                )
                continue

        try:
            time_s = float(event["time_s"])
            node_id = int(event["node_id"])
        except (TypeError, ValueError) as exc:
            anomaly_count += 1
            warnings.warn(
                f"Événement invalide ignoré à l'index {idx}: type invalide ({exc})",
                RuntimeWarning,
                stacklevel=2,
            )
            continue

        sf = int(event.get("sf", 7) or 7)
        snr_db = float(event.get("snr_db", 0.0) or 0.0)
        sinr_db = float(event.get("sinr_db", snr_db) or 0.0)
        threshold_db = float(event.get("threshold_db", 0.0) or 0.0)
        success = int(bool(event.get("success", False)))
        delivered = int(bool(event.get("delivered", success)))
        payload_bytes = int(event.get("payload_bytes", 0) or 0)
        airtime_s = float(event.get("airtime_s", 0.0) or 0.0)
        outage = int(bool(event.get("outage", not success)))
        switch_count = int(event.get("switch_count", 0) or 0)
        previous_switch_count = node_previous_switch_count[node_id]
        switch_increment = max(switch_count - previous_switch_count, 0)
        node_previous_switch_count[node_id] = max(previous_switch_count, switch_count)
        regret_proxy = max(0.0, (1.0 if success else 1.25) + 0.08 * airtime_s - (1.0 - 0.08 * 0.03))
        exploration_rate = float(switch_increment > 0)
        decision_stability = 1.0 - exploration_rate
        decision_reason = str(event.get("decision_reason", "") or "")
        target_sf = int(event.get("target_sf", sf) or sf)
        generated_packets_total = int(event.get("generated_packets_total", 0) or 0)
        dropped_packets_total = int(event.get("dropped_packets_total", 0) or 0)
        buffer_occupancy = int(event.get("buffer_occupancy", 0) or 0)
        retry_attempt = int(event.get("retry_attempt", 0) or 0)

        row = {
            **scenario,
            "run_id": run_id,
            "event_idx": idx,
            "time_s": time_s,
            "event_type": event_type,
            "node_id": node_id,
            "sf": sf,
            "snr_db": snr_db,
            "sinr_db": sinr_db,
            "threshold_db": threshold_db,
            "success": success,
            "delivered": delivered,
            "payload_bytes": payload_bytes,
            "airtime_s": airtime_s,
            "outage": outage,
            "switch_count": switch_count,
            "regret_proxy": regret_proxy,
            "exploration_rate": exploration_rate,
            "decision_stability": decision_stability,
            "decision_reason": decision_reason,
            "target_sf": target_sf,
            "generated_packets_total": generated_packets_total,
            "dropped_packets_total": dropped_packets_total,
            "buffer_occupancy": buffer_occupancy,
            "retry_attempt": retry_attempt,
        }
        event_rows.append(row)

        if event_type == "packet_generated":
            bin_index = int(time_s // time_bin_s)
            if "generated_packets_total" in event:
                previous_total = node_generated_totals[node_id]
                generated_delta = max(generated_packets_total - previous_total, 0)
                node_generated_totals[node_id] = max(previous_total, generated_packets_total)
            else:
                generated_delta = 1
            generated_packets += generated_delta

        if event_type == "uplink":
            tx_count += 1
            success_count += success
            delivered_bytes += payload_bytes if delivered else 0
            outage_events += outage
            total_switch_count += switch_increment
            node_successes[node_id] += success
            node_airtime[node_id] += airtime_s

            bin_index = int(time_s // time_bin_s)
            key = (bin_index, node_id)
            if key not in bins:
                bins[key] = {
                    **scenario,
                    "run_id": run_id,
                    "bin_start_s": bin_index * time_bin_s,
                    "bin_end_s": (bin_index + 1) * time_bin_s,
                    "node_id": node_id,
                    "tx_count": 0,
                    "success_count": 0,
                    "snr_sum": 0.0,
                    "sinr_sum": 0.0,
                    "airtime_s": 0.0,
                    "outage_count": 0,
                    "switch_count": 0,
                    "regret_proxy_sum": 0.0,
                    "exploration_sum": 0.0,
                    "decision_stability_sum": 0.0,
                    "delivered_bytes": 0,
                }
            slot = bins[key]
            slot["tx_count"] += 1
            slot["success_count"] += success
            slot["snr_sum"] += snr_db
            slot["sinr_sum"] += sinr_db
            slot["airtime_s"] += airtime_s
            slot["outage_count"] += outage
            slot["switch_count"] += switch_increment
            slot["regret_proxy_sum"] += regret_proxy
            slot["exploration_sum"] += exploration_rate
            slot["decision_stability_sum"] += decision_stability
            slot["delivered_bytes"] += payload_bytes if delivered else 0

    if anomaly_count:
        warnings.warn(
            f"{anomaly_count} événement(s) invalide(s) ignoré(s) pendant l'écriture du run {run_id}.",
            RuntimeWarning,
            stacklevel=2,
        )

    _write_csv(run_dir / "events.csv", EVENT_COLUMNS, event_rows)

    node_timeseries_rows: list[dict[str, Any]] = []
    for (_, _), slot in sorted(bins.items(), key=lambda item: (item[0][0], item[0][1])):
        tx = int(slot["tx_count"])
        success = int(slot["success_count"])
        duration = float(slot["bin_end_s"] - slot["bin_start_s"])
        node_timeseries_rows.append(
            {
                **scenario,
                "run_id": run_id,
                "bin_start_s": slot["bin_start_s"],
                "bin_end_s": slot["bin_end_s"],
                "node_id": slot["node_id"],
                "tx_count": tx,
                "success_count": success,
                "delivery_ratio": der(success, tx),
                "throughput_bps": throughput(int(slot["delivered_bytes"]), duration),
                "mean_snr_db": slot["snr_sum"] / max(tx, 1),
                "mean_sinr_db": slot["sinr_sum"] / max(tx, 1),
                "airtime_s": slot["airtime_s"],
                "outage_count": slot["outage_count"],
                "switch_count": slot["switch_count"],
                "regret_proxy_mean": slot["regret_proxy_sum"] / max(tx, 1),
                "exploration_rate_mean": slot["exploration_sum"] / max(tx, 1),
                "decision_stability_mean": slot["decision_stability_sum"] / max(tx, 1),
            }
        )
    _write_csv(run_dir / "node_timeseries.csv", NODE_TIMESERIES_COLUMNS, node_timeseries_rows)

    node_ids = {int(row["node_id"]) for row in event_rows if int(row["node_id"]) >= 0}
    airtime_total = sum(float(v) for v in node_airtime.values())

    pdr_by_bin: dict[int, dict[str, int]] = defaultdict(lambda: {"tx": 0, "success": 0})
    for row in node_timeseries_rows:
        bin_index = int(float(row["bin_start_s"]) // time_bin_s)
        pdr_by_bin[bin_index]["tx"] += int(row["tx_count"])
        pdr_by_bin[bin_index]["success"] += int(row["success_count"])

    pdr_series: list[float] = []
    for bin_index in sorted(pdr_by_bin):
        bucket = pdr_by_bin[bin_index]
        pdr_series.append(pdr(bucket["success"], bucket["tx"]))

    pdr_binary_series = [1.0 if value >= (1.0 - TC_PROTOCOL_TOLERANCE) else 0.0 for value in pdr_series]
    tc_from_timeseries = convergence_tc(
        pdr_binary_series,
        dt_s=tc_dt_s,
        stationary_tail_bins=TC_PROTOCOL_STABLE_BINS,
        target_ratio=1.0 - TC_PROTOCOL_TOLERANCE,
    )

    fairness_node_successes = [float(node_successes[node_id]) for node_id in sorted(node_ids)]

    summary_row = {
        **scenario,
        "run_id": run_id,
        "duration_s": duration_s,
        "node_count": len(node_ids),
        "tx_count": tx_count,
        "success_count": success_count,
        "generated_packets": generated_packets,
        "delivered_bytes": delivered_bytes,
        "pdr": pdr(success_count, tx_count),
        "der": der(success_count, generated_packets),
        "throughput_bps": throughput(delivered_bytes, duration_s),
        "Tc_s": tc_from_timeseries,
        "tc_method": tc_method,
        "tc_dt_s": tc_dt_s,
        "jain_fairness": jain_fairness(fairness_node_successes),
        "airtime_total_s": airtime_total,
        "airtime_mean_per_node_s": airtime_total / max(len(node_ids), 1),
        "outage_ratio": outage_ratio(outage_events, tx_count),
        "switch_count": total_switch_count,
    }
    _write_csv(run_dir / "summary.csv", SUMMARY_COLUMNS, [summary_row])

    return {
        "run_dir": run_dir,
        "run_config": run_config_path,
        "events": run_dir / "events.csv",
        "node_timeseries": run_dir / "node_timeseries.csv",
        "summary": run_dir / "summary.csv",
    }



def _iter_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def _collect_run_dirs(paths: Iterable[Path]) -> list[Path]:
    run_dirs: list[Path] = []
    for path in paths:
        if path.is_file() and path.name == "summary.csv":
            run_dirs.append(path.parent)
            continue
        if path.is_dir() and ((path / "summary.csv").is_file() or (path / "events.csv").is_file()):
            run_dirs.append(path)
            continue
        if path.is_dir() and (path / "results").is_dir():
            for candidate in sorted((path / "results").iterdir()):
                if candidate.is_dir():
                    run_dirs.append(candidate)
    unique = []
    seen = set()
    for item in run_dirs:
        resolved = item.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(item)
    return unique


def _missing_required_files(run_dir: Path, *, summary_only: bool) -> list[str]:
    required_files = ["summary.csv"]
    if not summary_only:
        required_files.append("events.csv")
    return [name for name in required_files if not (run_dir / name).is_file()]


def _validate_sinr_cdf_group(
    *,
    key: tuple[str, ...],
    quantiles: list[float],
    sinrs: list[float],
    factor_columns: list[str],
) -> None:
    context = ", ".join(f"{column}={value}" for column, value in zip(factor_columns, key, strict=False))
    if any(curr <= prev for prev, curr in zip(quantiles, quantiles[1:], strict=False)):
        raise ValueError(f"sinr_cdf invalide: quantiles non strictement croissants ({context})")
    if any(curr < prev for prev, curr in zip(sinrs, sinrs[1:], strict=False)):
        raise ValueError(f"sinr_cdf invalide: sinr_db non monotone ({context})")


def _build_sinr_quantile_grid(*, step: float) -> list[float]:
    if not math.isfinite(step) or step <= 0.0 or step > 1.0:
        raise ValueError("sinr_quantile_step doit être dans ]0, 1].")

    grid: list[float] = []
    index = 1
    while True:
        quantile = min(index * step, 1.0)
        if grid and math.isclose(quantile, grid[-1], rel_tol=0.0, abs_tol=1e-12):
            break
        grid.append(quantile)
        if math.isclose(quantile, 1.0, rel_tol=0.0, abs_tol=1e-12):
            break
        index += 1
    return grid


def _resolve_sinr_cdf_quantile_step(
    *,
    sinr_quantile_step: float,
    sinr_cdf_granularity: float | None,
) -> float:
    """Résout le pas de quantile CDF à utiliser.

    ``sinr_cdf_granularity`` est l'option recommandée (plus explicite côté API).
    ``sinr_quantile_step`` est conservé pour compatibilité rétro.
    """

    if sinr_cdf_granularity is None:
        return sinr_quantile_step
    if not math.isclose(sinr_cdf_granularity, sinr_quantile_step, rel_tol=0.0, abs_tol=1e-12):
        warnings.warn(
            (
                "sinr_cdf_granularity est prioritaire sur sinr_quantile_step "
                f"({sinr_cdf_granularity:.6g} vs {sinr_quantile_step:.6g})."
            ),
            RuntimeWarning,
            stacklevel=2,
        )
    return sinr_cdf_granularity


def _nearest_rank_quantile(sorted_values: list[float], quantile: float) -> float:
    if not sorted_values:
        raise ValueError("quantile demandé sur une série vide")
    rank = max(1, math.ceil(quantile * len(sorted_values)))
    return sorted_values[rank - 1]


def _validate_sinr_cdf_comparability(
    *,
    by_context: Mapping[tuple[str, ...], Mapping[str, list[float]]],
    factor_columns: list[str],
) -> None:
    context_columns = [column for column in factor_columns if column != "algo"]
    for context_key, grids_by_algo in by_context.items():
        baseline_algo = ""
        baseline_grid: list[float] | None = None
        for algo, grid in sorted(grids_by_algo.items()):
            if baseline_grid is None:
                baseline_algo = algo
                baseline_grid = grid
                continue
            if len(grid) != len(baseline_grid) or any(
                not math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)
                for left, right in zip(grid, baseline_grid, strict=False)
            ):
                context = ", ".join(
                    f"{column}={value}" for column, value in zip(context_columns, context_key, strict=False)
                )
                raise ValueError(
                    "sinr_cdf invalide: grille de quantiles incohérente entre algorithmes "
                    f"({context}, baseline={baseline_algo}, algo={algo})."
                )


def aggregate_runs(
    *,
    inputs: Iterable[Path],
    output_root: Path,
    summary_only: bool = False,
    skip_sinr_cdf: bool = False,
    skip_sf_distribution: bool = False,
    strict: bool = False,
    verbose: bool = False,
    verbose_warnings: bool = False,
    sinr_quantile_step: float = DEFAULT_SINR_CDF_QUANTILE_STEP,
    sinr_cdf_granularity: float | None = None,
    ignored_runs_report: list[dict[str, str]] | None = None,
    sinr_cdf_metadata: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Agrège des runs et écrit les CSV dans ``aggregates/``."""

    run_dirs = _collect_run_dirs(inputs)
    out_dir = output_root / "aggregates"
    out_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_path = out_dir / "aggregate_diagnostics.json"

    if not run_dirs:
        verification_hint = "python -m mobilesfrdth.cli aggregate --results <dossier_résultats> --out <dossier_sortie> --verbose"
        raise ValueError(
            "Aucun dossier de run détecté dans les entrées. "
            "Vérifiez que vos runs sont sous <input>/results/<run_id>/. "
            f"Commande de vérification: {verification_hint}"
        )

    if summary_only:
        skip_sinr_cdf = True
        skip_sf_distribution = True

    sinr_quantile_grid: list[float] = []
    effective_sinr_quantile_step = _resolve_sinr_cdf_quantile_step(
        sinr_quantile_step=sinr_quantile_step,
        sinr_cdf_granularity=sinr_cdf_granularity,
    )
    if not skip_sinr_cdf:
        sinr_quantile_grid = _build_sinr_quantile_grid(step=effective_sinr_quantile_step)

    metric_names = [
        "pdr",
        "der",
        "throughput_bps",
        "Tc_s",
        "jain_fairness",
        "airtime_total_s",
        "outage_ratio",
        "switch_count",
    ]
    metric_accumulators: dict[tuple[str, ...], dict[str, list[float]]] = defaultdict(
        lambda: {name: [] for name in metric_names}
    )
    sf_counter: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    sinr_values: dict[tuple[str, ...], list[float]] = defaultdict(list)

    factor_columns = ["N", "speed", "mobility_model", "mode", "algo", "gateways", "sigma_shadowing"]
    factor_aliases: dict[str, tuple[str, ...]] = {
        "N": ("N",),
        "speed": ("speed",),
        "mobility_model": ("mobility_model", "model"),
        "mode": ("mode",),
        "algo": ("algo",),
        "gateways": ("gateways",),
        "sigma_shadowing": ("sigma_shadowing", "sigma"),
    }

    def _factor_value(row: Mapping[str, str], column: str) -> str:
        for alias in factor_aliases[column]:
            if alias in row and row.get(alias, "") != "":
                return row.get(alias, "")
        return ""

    convergence_path = out_dir / "convergence_tc.csv"
    fairness_path = out_dir / "fairness_airtime_switching.csv"
    ucb_tracking_path = out_dir / "ucb_tracking.csv"
    pareto_reliability_airtime_path = out_dir / "pareto_reliability_airtime.csv"
    outage_probability_path = out_dir / "outage_probability.csv"
    energy_efficiency_reliability_path = out_dir / "energy_efficiency_reliability.csv"

    convergence_handle = convergence_path.open("w", newline="", encoding="utf-8")
    fairness_handle = fairness_path.open("w", newline="", encoding="utf-8")
    convergence_writer = csv.DictWriter(convergence_handle, fieldnames=SCENARIO_ID_COLUMNS + ["run_id", "Tc_s"])
    fairness_writer = csv.DictWriter(
        fairness_handle,
        fieldnames=SCENARIO_ID_COLUMNS + ["run_id", "jain_fairness", "airtime_total_s", "switch_count"],
    )
    convergence_writer.writeheader()
    fairness_writer.writeheader()

    ucb_tracking_rows: list[dict[str, Any]] = []

    total = len(run_dirs)
    processed = 0
    skipped = 0
    ignored_runs: list[dict[str, str]] = []
    complete_runs: list[dict[str, str]] = []
    incomplete_runs: list[dict[str, str]] = []
    warning_groups: dict[str, list[dict[str, str]]] = defaultdict(list)

    def _record_warning(*, category: str, message: str, run_id: str, run_dir: Path) -> None:
        warning_groups[category].append(
            {
                "run_id": run_id,
                "run_dir": str(run_dir),
                "message": message,
            }
        )

    def _warning_runs(entries: list[dict[str, str]]) -> list[str]:
        unique_ids: list[str] = []
        seen: set[str] = set()
        for item in entries:
            run_id = str(item.get("run_id", "") or "").strip()
            if not run_id or run_id in seen:
                continue
            seen.add(run_id)
            unique_ids.append(run_id)
        return unique_ids

    def _format_warning_summary(category: str, entries: list[dict[str, str]], *, max_examples: int = 3) -> str:
        run_ids = _warning_runs(entries)
        count = len(run_ids)
        sample_ids = run_ids[:max_examples]
        if sample_ids:
            return f"{count} run(s) {category} (exemples: {', '.join(sample_ids)})."
        return f"{count} run(s) {category}."

    def _record_incomplete(*, run_dir: Path, reason: str, details: str) -> None:
        nonlocal skipped
        skipped += 1
        entry = {"run_dir": str(run_dir), "reason": reason, "details": details}
        ignored_runs.append(entry)
        incomplete_runs.append(entry)

    def _write_diagnostics() -> None:
        warning_run_counts = {
            category: len(_warning_runs(entries))
            for category, entries in warning_groups.items()
        }
        diagnostics_payload = {
            "complete_runs": complete_runs,
            "incomplete_runs": incomplete_runs,
            "warning_counts": {category: len(entries) for category, entries in warning_groups.items()},
            "warning_run_counts": warning_run_counts,
            "warning_details": warning_groups,
            "counts": {
                "discovered_runs": total,
                "valid_runs": processed,
                "incomplete_runs": len(incomplete_runs),
            },
        }
        diagnostics_path.write_text(json.dumps(diagnostics_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _coerce_float(value: Any, *, field: str, allow_inf: bool = False) -> float:
        try:
            parsed = float(value or 0.0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"valeur non numérique pour '{field}' ({value!r})") from exc
        if math.isinf(parsed) and allow_inf:
            return parsed
        if not math.isfinite(parsed):
            raise ValueError(f"valeur non finie pour '{field}' ({value!r})")
        return parsed
    for index, run_dir in enumerate(run_dirs, start=1):
        if verbose:
            print(f"{index}/{total} run dirs traités", end="\r" if index < total else "\n", flush=True)
        missing_files = _missing_required_files(run_dir, summary_only=summary_only)
        if missing_files:
            message = (
                f"Run incomplet ignoré: {run_dir} (fichier(s) manquant(s): {', '.join(sorted(missing_files))})"
            )
            if strict:
                raise FileNotFoundError(message)
            run_id = run_dir.name
            _record_warning(
                category="incomplets/corrompus ignorés",
                message=message,
                run_id=run_id,
                run_dir=run_dir,
            )
            if verbose_warnings:
                warnings.warn(message, RuntimeWarning, stacklevel=2)
            missing_set = set(missing_files)
            if "summary.csv" in missing_set:
                reason = "summary_absent"
            elif "events.csv" in missing_set:
                reason = "events_absent"
            else:
                reason = "missing_files"
            _record_incomplete(run_dir=run_dir, reason=reason, details=", ".join(sorted(missing_files)))
            continue

        summary_rows = list(_iter_csv(run_dir / "summary.csv"))
        if not summary_rows:
            message = f"Run corrompu ignoré: {run_dir} (summary.csv vide)"
            if strict:
                raise ValueError(message)
            run_id = run_dir.name
            _record_warning(
                category="incomplets/corrompus ignorés",
                message=message,
                run_id=run_id,
                run_dir=run_dir,
            )
            if verbose_warnings:
                warnings.warn(message, RuntimeWarning, stacklevel=2)
            _record_incomplete(run_dir=run_dir, reason="csv_corrupted", details="summary.csv vide")
            continue

        valid_summary_rows: list[Mapping[str, str]] = []
        parsed_summary_values: list[tuple[tuple[str, ...], dict[str, float]]] = []
        run_rejected = False
        for row in summary_rows:
            try:
                key = tuple(_factor_value(row, column) for column in factor_columns)
                tc_dt_raw = row.get("tc_dt_s", "")
                tc_dt_s = TC_PROTOCOL_DT_S if tc_dt_raw in ("", None) else _coerce_float(tc_dt_raw, field="tc_dt_s")
                tc_method = str(row.get("tc_method", "protocol_dt") or "protocol_dt")
                parsed_metrics: dict[str, float] = {}
                for metric_name in metric_names:
                    parsed_metrics[metric_name] = _coerce_float(
                        row.get(metric_name, 0.0),
                        field=metric_name,
                        allow_inf=metric_name == "Tc_s",
                    )
            except ValueError as exc:
                message = f"Run corrompu ignoré: {run_dir} ({exc})"
                if strict:
                    raise ValueError(message) from exc
                run_id = str(row.get("run_id", run_dir.name))
                _record_warning(
                    category="incomplets/corrompus ignorés",
                    message=message,
                    run_id=run_id,
                    run_dir=run_dir,
                )
                if verbose_warnings:
                    warnings.warn(message, RuntimeWarning, stacklevel=2)
                _record_incomplete(run_dir=run_dir, reason="csv_corrupted", details=f"summary.csv: {exc}")
                break

            if not math.isclose(tc_dt_s, TC_PROTOCOL_DT_S, rel_tol=0.0, abs_tol=1e-9):
                warning_message = (
                    f"Run {run_dir} utilise tc_dt_s={tc_dt_s:.6g}s (méthode '{tc_method}') "
                    f"au lieu du protocole {TC_PROTOCOL_DT_S:.1f}s."
                )
                run_id = str(row.get("run_id", run_dir.name))
                _record_warning(
                    category=f"utilisent tc_dt_s!= {TC_PROTOCOL_DT_S:.1f}s",
                    message=warning_message,
                    run_id=run_id,
                    run_dir=run_dir,
                )
                if verbose_warnings:
                    warnings.warn(f"Batch: {warning_message}", RuntimeWarning, stacklevel=2)

            valid_summary_rows.append(row)
            parsed_summary_values.append((key, parsed_metrics))

        if not valid_summary_rows:
            continue

        run_sinr_values: dict[tuple[str, ...], list[float]] = defaultdict(list)
        run_sf_counter: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
        run_uplinks: list[dict[str, str]] = []

        if not summary_only:
            try:
                for row in _iter_csv(run_dir / "events.csv"):
                    if row.get("event_type") != "uplink":
                        continue
                    key = tuple(_factor_value(row, column) for column in factor_columns)
                    if not skip_sf_distribution:
                        run_sf_counter[key][row.get("sf", "")] += 1
                    if not skip_sinr_cdf:
                        run_sinr_values[key].append(_coerce_float(row.get("sinr_db", 0.0), field="sinr_db"))
                    run_uplinks.append(row)
            except ValueError as exc:
                message = f"Run corrompu ignoré: {run_dir} (events.csv: {exc})"
                if strict:
                    raise ValueError(message) from exc
                run_id = str(valid_summary_rows[0].get("run_id", run_dir.name))
                _record_warning(
                    category="incomplets/corrompus ignorés",
                    message=message,
                    run_id=run_id,
                    run_dir=run_dir,
                )
                if verbose_warnings:
                    warnings.warn(message, RuntimeWarning, stacklevel=2)
                _record_incomplete(run_dir=run_dir, reason="csv_corrupted", details=f"events.csv: {exc}")
                run_rejected = True

        if run_rejected:
            continue

        for row in valid_summary_rows:
            scenario_row = {column: row.get(column, "") for column in SCENARIO_ID_COLUMNS}
            if scenario_row.get("sigma_shadowing", "") == "":
                scenario_row["sigma_shadowing"] = row.get("sigma", "")
            convergence_writer.writerow(
                {
                    **scenario_row,
                    "run_id": row.get("run_id", ""),
                    "Tc_s": row.get("Tc_s", ""),
                }
            )
            fairness_writer.writerow(
                {
                    **scenario_row,
                    "run_id": row.get("run_id", ""),
                    "jain_fairness": row.get("jain_fairness", ""),
                    "airtime_total_s": row.get("airtime_total_s", ""),
                    "switch_count": row.get("switch_count", ""),
                }
            )

        for key, parsed_metrics in parsed_summary_values:
            bucket = metric_accumulators[key]
            for metric_name, metric_value in parsed_metrics.items():
                bucket[metric_name].append(metric_value)

        processed += 1
        complete_runs.append({"run_dir": str(run_dir), "run_id": str(valid_summary_rows[0].get("run_id", ""))})

        if summary_only:
            continue

        for key, counts in run_sf_counter.items():
            sf_counter[key].update(counts)
        for key, run_values in run_sinr_values.items():
            sinr_values[key].extend(run_values)

        run_summary = valid_summary_rows[0]
        if run_summary is None:
            continue
        run_algo = str(run_summary.get("algo", "")).lower()
        if run_algo not in {"ucb", "ucb_forget"}:
            continue
        uplinks = run_uplinks
        if not uplinks:
            continue
        ucb_tracking_rows.append(
            {
                "speed": run_summary.get("speed", ""),
                "mode": run_summary.get("mode", ""),
                "algo": run_algo,
                "run_id": run_summary.get("run_id", ""),
                "Tc_s": run_summary.get("Tc_s", ""),
                "regret_proxy_mean": sum(float(row.get("regret_proxy", 0.0) or 0.0) for row in uplinks) / len(uplinks),
                "exploration_rate_mean": sum(float(row.get("exploration_rate", 0.0) or 0.0) for row in uplinks) / len(uplinks),
                "decision_stability_mean": sum(float(row.get("decision_stability", 0.0) or 0.0) for row in uplinks) / len(uplinks),
            }
        )

    convergence_handle.close()
    fairness_handle.close()

    _write_diagnostics()

    if processed == 0:
        verification_hint = "python -m mobilesfrdth.cli aggregate --results <dossier_résultats> --out <dossier_sortie> --verbose"
        if total == 0:
            raise ValueError(
                "Aucun run trouvé. "
                "Vérifiez l'arborescence des entrées et relancez avec: "
                f"{verification_hint}"
            )
        raise ValueError(
            "Runs détectés mais aucun run valide à agréger (incomplets/corrompus). "
            f"Consultez {diagnostics_path} et vérifiez avec: {verification_hint}"
        )

    for category, entries in warning_groups.items():
        if not entries:
            continue
        warnings.warn(
            f"{_format_warning_summary(category, entries)} Détails complets: {diagnostics_path}",
            RuntimeWarning,
            stacklevel=2,
        )

    print(f"Dossiers traités: {processed}/{total}")
    if skipped:
        print(f"Runs incomplets ignorés: {skipped}")

    metric_by_factor_rows = []
    algo_index = factor_columns.index("algo")
    distinct_groups_by_algo: dict[str, int] = {}
    for key, bucket in sorted(metric_accumulators.items()):
        pdr_stats = _mean_std_ci95_stats(bucket["pdr"])
        der_stats = _mean_std_ci95_stats(bucket["der"])
        throughput_stats = _mean_std_ci95_stats(bucket["throughput_bps"])
        tc_stats = _mean_std_ci95_stats(bucket["Tc_s"], allow_inf=True)
        jain_stats = _mean_std_ci95_stats(bucket["jain_fairness"])
        airtime_stats = _mean_std_ci95_stats(bucket["airtime_total_s"])
        outage_stats = _mean_std_ci95_stats(bucket["outage_ratio"])
        switch_stats = _mean_std_ci95_stats(bucket["switch_count"])
        num_runs = int(pdr_stats["n"])

        metric_by_factor_rows.append(
            {
                **dict(zip(factor_columns, key, strict=False)),
                "n_runs_effective": num_runs,
                "num_runs": num_runs,
                "pdr_mean": pdr_stats["mean"],
                "pdr_std": pdr_stats["std"],
                "pdr_n": int(pdr_stats["n"]),
                "pdr_ci95": pdr_stats["ci95"],
                "pdr_ci95_low": pdr_stats["ci95_low"],
                "pdr_ci95_high": pdr_stats["ci95_high"],
                "der_mean": der_stats["mean"],
                "der_std": der_stats["std"],
                "der_n": int(der_stats["n"]),
                "der_ci95": der_stats["ci95"],
                "der_ci95_low": der_stats["ci95_low"],
                "der_ci95_high": der_stats["ci95_high"],
                "throughput_bps_mean": throughput_stats["mean"],
                "throughput_bps_std": throughput_stats["std"],
                "throughput_bps_n": int(throughput_stats["n"]),
                "throughput_bps_ci95": throughput_stats["ci95"],
                "throughput_bps_ci95_low": throughput_stats["ci95_low"],
                "throughput_bps_ci95_high": throughput_stats["ci95_high"],
                "Tc_s_mean": tc_stats["mean"],
                "Tc_s_std": tc_stats["std"],
                "Tc_s_n": int(tc_stats["n"]),
                "Tc_s_ci95": tc_stats["ci95"],
                "Tc_s_ci95_low": tc_stats["ci95_low"],
                "Tc_s_ci95_high": tc_stats["ci95_high"],
                "jain_fairness_mean": jain_stats["mean"],
                "jain_fairness_std": jain_stats["std"],
                "jain_fairness_n": int(jain_stats["n"]),
                "jain_fairness_ci95": jain_stats["ci95"],
                "jain_fairness_ci95_low": jain_stats["ci95_low"],
                "jain_fairness_ci95_high": jain_stats["ci95_high"],
                "airtime_total_s_mean": airtime_stats["mean"],
                "airtime_total_s_ci95": airtime_stats["ci95"],
                "outage_ratio_mean": outage_stats["mean"],
                "outage_ratio_std": outage_stats["std"],
                "outage_ratio_n": int(outage_stats["n"]),
                "outage_ratio_ci95": outage_stats["ci95"],
                "outage_ratio_ci95_low": outage_stats["ci95_low"],
                "outage_ratio_ci95_high": outage_stats["ci95_high"],
                "switch_count_mean": switch_stats["mean"],
                "switch_count_ci95": switch_stats["ci95"],
            }
        )

    for key in metric_accumulators:
        algo = key[algo_index]
        distinct_groups_by_algo[algo] = distinct_groups_by_algo.get(algo, 0) + 1

    if sum(distinct_groups_by_algo.values()) != len(metric_by_factor_rows):
        raise ValueError(
            "Agrégation incohérente: des groupes ont été perdus lors de la construction de metric_by_factor.csv "
            "(dimension algo potentiellement écrasée)."
        )

    metric_by_factor_path = out_dir / "metric_by_factor.csv"
    _write_csv(metric_by_factor_path, factor_columns + [
        "n_runs_effective",
        "num_runs",
        "pdr_mean",
        "pdr_std",
        "pdr_n",
        "pdr_ci95",
        "pdr_ci95_low",
        "pdr_ci95_high",
        "der_mean",
        "der_std",
        "der_n",
        "der_ci95",
        "der_ci95_low",
        "der_ci95_high",
        "throughput_bps_mean",
        "throughput_bps_std",
        "throughput_bps_n",
        "throughput_bps_ci95",
        "throughput_bps_ci95_low",
        "throughput_bps_ci95_high",
        "Tc_s_mean",
        "Tc_s_std",
        "Tc_s_n",
        "Tc_s_ci95",
        "Tc_s_ci95_low",
        "Tc_s_ci95_high",
        "jain_fairness_mean",
        "jain_fairness_std",
        "jain_fairness_n",
        "jain_fairness_ci95",
        "jain_fairness_ci95_low",
        "jain_fairness_ci95_high",
        "airtime_total_s_mean",
        "airtime_total_s_ci95",
        "outage_ratio_mean",
        "outage_ratio_std",
        "outage_ratio_n",
        "outage_ratio_ci95",
        "outage_ratio_ci95_low",
        "outage_ratio_ci95_high",
        "switch_count_mean",
        "switch_count_ci95",
    ], metric_by_factor_rows)

    files: dict[str, Path] = {"metric_by_factor": metric_by_factor_path}

    pareto_rows: list[dict[str, Any]] = []
    outage_probability_rows: list[dict[str, Any]] = []
    energy_efficiency_rows: list[dict[str, Any]] = []
    for row in metric_by_factor_rows:
        pdr_mean = float(row.get("pdr_mean", 0.0) or 0.0)
        pdr_ci95 = float(row.get("pdr_ci95", 0.0) or 0.0)
        airtime_mean = float(row.get("airtime_total_s_mean", 0.0) or 0.0)
        airtime_ci95 = float(row.get("airtime_total_s_ci95", 0.0) or 0.0)
        throughput_mean = float(row.get("throughput_bps_mean", 0.0) or 0.0)
        throughput_ci95 = float(row.get("throughput_bps_ci95", 0.0) or 0.0)
        outage_mean = float(row.get("outage_ratio_mean", 0.0) or 0.0)
        outage_ci95 = float(row.get("outage_ratio_ci95", 0.0) or 0.0)
        efficiency_mean = throughput_mean / airtime_mean if airtime_mean > 0 else 0.0
        efficiency_ci95 = 0.0
        if throughput_mean > 0 and airtime_mean > 0:
            efficiency_ci95 = abs(efficiency_mean) * math.sqrt(
                (throughput_ci95 / max(throughput_mean, 1e-12)) ** 2 + (airtime_ci95 / max(airtime_mean, 1e-12)) ** 2
            )

        pareto_rows.append(
            {
                "N": row.get("N", ""),
                "speed": row.get("speed", ""),
                "mobility_model": row.get("mobility_model", ""),
                "mode": row.get("mode", ""),
                "algo": row.get("algo", ""),
                "gateways": row.get("gateways", ""),
                "sigma_shadowing": row.get("sigma_shadowing", row.get("sigma", "")),
                "num_runs": row.get("num_runs", 0),
                "pdr_mean": pdr_mean,
                "pdr_ci95": pdr_ci95,
                "airtime_total_s_mean": airtime_mean,
                "airtime_total_s_ci95": airtime_ci95,
            }
        )

        energy_efficiency_rows.append(
            {
                "N": row.get("N", ""),
                "speed": row.get("speed", ""),
                "mobility_model": row.get("mobility_model", ""),
                "mode": row.get("mode", ""),
                "algo": row.get("algo", ""),
                "gateways": row.get("gateways", ""),
                "sigma_shadowing": row.get("sigma_shadowing", row.get("sigma", "")),
                "num_runs": row.get("num_runs", 0),
                "pdr_mean": pdr_mean,
                "pdr_ci95": pdr_ci95,
                "energy_efficiency_mean": efficiency_mean,
                "energy_efficiency_ci95": efficiency_ci95,
            }
        )

        if str(row.get("mode", "")).lower() == "snir_on":
            outage_probability_rows.append(
                {
                    "N": row.get("N", ""),
                    "speed": row.get("speed", ""),
                    "mobility_model": row.get("mobility_model", ""),
                    "mode": row.get("mode", ""),
                    "algo": row.get("algo", ""),
                    "gateways": row.get("gateways", ""),
                    "sigma_shadowing": row.get("sigma_shadowing", row.get("sigma", "")),
                    "num_runs": row.get("num_runs", 0),
                    "outage_prob_mean": outage_mean,
                    "outage_prob_ci95": outage_ci95,
                }
            )

    _write_csv(
        pareto_reliability_airtime_path,
        [
            "N",
            "speed",
            "mobility_model",
            "mode",
            "algo",
            "gateways",
            "sigma_shadowing",
            "num_runs",
            "pdr_mean",
            "pdr_ci95",
            "airtime_total_s_mean",
            "airtime_total_s_ci95",
        ],
        pareto_rows,
    )
    _write_csv(
        outage_probability_path,
        [
            "N",
            "speed",
            "mobility_model",
            "mode",
            "algo",
            "gateways",
            "sigma_shadowing",
            "num_runs",
            "outage_prob_mean",
            "outage_prob_ci95",
        ],
        outage_probability_rows,
    )
    _write_csv(
        energy_efficiency_reliability_path,
        [
            "N",
            "speed",
            "mobility_model",
            "mode",
            "algo",
            "gateways",
            "sigma_shadowing",
            "num_runs",
            "pdr_mean",
            "pdr_ci95",
            "energy_efficiency_mean",
            "energy_efficiency_ci95",
        ],
        energy_efficiency_rows,
    )
    files["pareto_reliability_airtime"] = pareto_reliability_airtime_path
    files["outage_probability"] = outage_probability_path
    files["energy_efficiency_reliability"] = energy_efficiency_reliability_path

    if not skip_sf_distribution:
        distribution_rows = []
        for key, counts in sorted(sf_counter.items()):
            total_count = sum(counts.values())
            for sf, count in sorted(counts.items(), key=lambda item: int(item[0] or 0)):
                distribution_rows.append(
                    {
                        **dict(zip(factor_columns, key, strict=False)),
                        "sf": sf,
                        "count": count,
                        "ratio": count / max(total_count, 1),
                    }
                )
        distribution_path = out_dir / "distribution_sf.csv"
        _write_csv(distribution_path, factor_columns + ["sf", "count", "ratio"], distribution_rows)
        files["distribution_sf"] = distribution_path

    if not skip_sinr_cdf:
        sinr_rows = []
        quantile_grid_by_context: dict[tuple[str, ...], dict[str, list[float]]] = defaultdict(dict)
        for key, values in sorted(sinr_values.items()):
            if not values:
                continue
            factors = dict(zip(factor_columns, key, strict=False))
            data = sorted(values)
            n = len(data)
            quantiles = list(sinr_quantile_grid)
            sinrs = [_nearest_rank_quantile(data, quantile) for quantile in quantiles]
            _validate_sinr_cdf_group(
                key=key,
                quantiles=quantiles,
                sinrs=sinrs,
                factor_columns=factor_columns,
            )
            context_key = tuple(factors[column] for column in factor_columns if column != "algo")
            quantile_grid_by_context[context_key][factors.get("algo", "")] = quantiles
            for quantile, sinr in zip(quantiles, sinrs, strict=False):
                sinr_rows.append(
                    {
                        **factors,
                        "quantile": quantile,
                        "sinr_db": sinr,
                        "sample_count": n,
                    }
                )
        _validate_sinr_cdf_comparability(by_context=quantile_grid_by_context, factor_columns=factor_columns)
        sinr_path = out_dir / "sinr_cdf.csv"
        _write_csv(sinr_path, factor_columns + ["quantile", "sinr_db", "sample_count"], sinr_rows)
        files["sinr_cdf"] = sinr_path
        if sinr_cdf_metadata is not None:
            sinr_cdf_metadata.update(
                {
                    "enabled": True,
                    "quantile_step": effective_sinr_quantile_step,
                    "num_quantiles": len(sinr_quantile_grid),
                    "quantile_min": sinr_quantile_grid[0] if sinr_quantile_grid else None,
                    "quantile_max": sinr_quantile_grid[-1] if sinr_quantile_grid else None,
                    "quantile_method": "nearest_rank",
                }
            )
    elif sinr_cdf_metadata is not None:
        sinr_cdf_metadata.update({"enabled": False})

    files["convergence_tc"] = convergence_path
    files["fairness_airtime_switching"] = fairness_path

    grouped_tracking: dict[tuple[str, str, str], dict[str, float]] = defaultdict(lambda: {
        "num_runs": 0.0,
        "num_runs_finite_tc": 0.0,
        "Tc_s_sum": 0.0,
        "regret_proxy_sum": 0.0,
        "exploration_rate_sum": 0.0,
        "decision_stability_sum": 0.0,
    })
    for row in ucb_tracking_rows:
        key = (str(row["speed"]), str(row["mode"]), str(row["algo"]))
        bucket = grouped_tracking[key]
        bucket["num_runs"] += 1.0
        tc_value = float(row.get("Tc_s", 0.0) or 0.0)
        if math.isfinite(tc_value):
            bucket["num_runs_finite_tc"] += 1.0
            bucket["Tc_s_sum"] += tc_value
        bucket["regret_proxy_sum"] += float(row.get("regret_proxy_mean", 0.0) or 0.0)
        bucket["exploration_rate_sum"] += float(row.get("exploration_rate_mean", 0.0) or 0.0)
        bucket["decision_stability_sum"] += float(row.get("decision_stability_mean", 0.0) or 0.0)

    ucb_tracking_aggregate_rows = []
    for (speed, mode, algo), bucket in sorted(grouped_tracking.items()):
        num_runs = max(int(bucket["num_runs"]), 1)
        ucb_tracking_aggregate_rows.append(
            {
                "speed": speed,
                "mode": mode,
                "algo": algo,
                "num_runs": num_runs,
                "Tc_s_mean": (
                    bucket["Tc_s_sum"] / bucket["num_runs_finite_tc"]
                    if bucket["num_runs_finite_tc"] > 0
                    else math.inf
                ),
                "regret_proxy_mean": bucket["regret_proxy_sum"] / num_runs,
                "exploration_rate_mean": bucket["exploration_rate_sum"] / num_runs,
                "decision_stability_mean": bucket["decision_stability_sum"] / num_runs,
            }
        )
    if not summary_only:
        _write_csv(
            ucb_tracking_path,
            ["speed", "mode", "algo", "num_runs", "Tc_s_mean", "regret_proxy_mean", "exploration_rate_mean", "decision_stability_mean"],
            ucb_tracking_aggregate_rows,
        )
        files["ucb_tracking"] = ucb_tracking_path

    if ignored_runs_report is not None:
        ignored_runs_report.extend(ignored_runs)

    return files


def summarize_run_completeness(inputs: Iterable[Path]) -> dict[str, int | None]:
    """Retourne un état de complétude entre runs trouvés et jobs attendus."""

    run_dirs = _collect_run_dirs(inputs)
    found_runs = sum(1 for run_dir in run_dirs if (run_dir / "summary.csv").is_file())

    expected_runs = 0
    has_jobs_manifest = False
    for path in inputs:
        jobs_candidates: list[Path] = []
        if path.is_file() and path.name == "jobs.json":
            jobs_candidates.append(path)
        if path.is_dir():
            direct = path / "jobs.json"
            nested = path / "results" / "jobs.json"
            if direct.is_file():
                jobs_candidates.append(direct)
            if nested.is_file():
                jobs_candidates.append(nested)

        for jobs_path in jobs_candidates:
            with jobs_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, Mapping):
                raise ValueError(f"Format JSON inattendu dans {jobs_path} (objet requis).")
            num_jobs = payload.get("num_jobs")
            if not isinstance(num_jobs, int):
                raise ValueError(f"Champ num_jobs manquant ou invalide dans {jobs_path}.")
            expected_runs += num_jobs
            has_jobs_manifest = True

    if not has_jobs_manifest:
        return {
            "expected_runs": None,
            "found_runs": found_runs,
            "missing_runs": 0,
        }

    return {
        "expected_runs": expected_runs,
        "found_runs": found_runs,
        "missing_runs": max(expected_runs - found_runs, 0),
    }

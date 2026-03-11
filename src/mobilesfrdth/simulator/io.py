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

from .metrics import convergence_tc_performance, der, jain_fairness, outage_ratio, pdr, throughput

SCENARIO_ID_COLUMNS = ["N", "speed", "mobility_model", "mode", "algo", "gateways", "sigma", "seed", "rep"]
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
    "jain_fairness",
    "airtime_total_s",
    "airtime_mean_per_node_s",
    "outage_ratio",
    "switch_count",
]


def _scenario_row(run_config: Mapping[str, Any]) -> dict[str, Any]:
    return {key: run_config.get(key, "") for key in SCENARIO_ID_COLUMNS}


def _coerce_event(event: Any) -> dict[str, Any]:
    if isinstance(event, Mapping):
        return dict(event)
    payload: dict[str, Any] = {
        "time_s": getattr(event, "time_s", 0.0),
        "event_type": getattr(event, "kind", "uplink"),
        "node_id": getattr(event, "node_id", -1),
    }
    for field in ("sf", "snr_db", "sinr_db", "threshold_db", "success", "delivered", "payload_bytes", "airtime_s", "outage", "switch_count", "decision_reason", "target_sf"):
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


def write_run_outputs(
    *,
    output_root: Path,
    run_id: str,
    run_config: Mapping[str, Any],
    events: Iterable[Any],
    duration_s: float,
    time_bin_s: float = 10.0,
) -> dict[str, Path]:
    """Écrit les artefacts d'un run dans ``results/<run_id>/``."""

    if duration_s <= 0:
        raise ValueError("duration_s doit être > 0")
    if time_bin_s <= 0:
        raise ValueError("time_bin_s doit être > 0")

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

    for idx, item in enumerate(events):
        event = _coerce_event(item)
        event_type = str(event.get("event_type", "uplink"))
        time_s = float(event.get("time_s", 0.0))
        node_id = int(event.get("node_id", -1))
        sf = int(event.get("sf", 7) or 7)
        snr_db = float(event.get("snr_db", 0.0) or 0.0)
        sinr_db = float(event.get("sinr_db", snr_db) or 0.0)
        threshold_db = float(event.get("threshold_db", 0.0) or 0.0)
        success = int(bool(event.get("success", event_type == "uplink")))
        delivered = int(bool(event.get("delivered", success)))
        payload_bytes = int(event.get("payload_bytes", 0) or 0)
        airtime_s = float(event.get("airtime_s", 0.0) or 0.0)
        outage = int(bool(event.get("outage", not success)))
        switch_count = int(event.get("switch_count", 0) or 0)
        regret_proxy = max(0.0, (1.0 if success else 1.25) + 0.08 * airtime_s - (1.0 - 0.08 * 0.03))
        exploration_rate = float(switch_count > 0)
        decision_stability = 1.0 - exploration_rate
        decision_reason = str(event.get("decision_reason", "") or "")
        target_sf = int(event.get("target_sf", sf) or sf)

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
        }
        event_rows.append(row)

        if event_type == "uplink":
            tx_count += 1
            generated_packets += 1
            success_count += success
            delivered_bytes += payload_bytes if delivered else 0
            outage_events += outage
            total_switch_count += switch_count
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
            slot["switch_count"] += switch_count
            slot["regret_proxy_sum"] += regret_proxy
            slot["exploration_sum"] += exploration_rate
            slot["decision_stability_sum"] += decision_stability
            slot["delivered_bytes"] += payload_bytes if delivered else 0

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
    der_series: list[float] = []
    cumulative_tx = 0
    cumulative_success = 0
    cumulative_generated = 0
    for bin_index in sorted(pdr_by_bin):
        bucket = pdr_by_bin[bin_index]
        pdr_series.append(pdr(bucket["success"], bucket["tx"]))
        cumulative_tx += int(bucket["tx"])
        cumulative_success += int(bucket["success"])
        cumulative_generated += int(bucket["tx"])
        der_series.append(der(cumulative_success, cumulative_generated))

    stationary_tail_bins = max(1, math.ceil(len(pdr_series) * 0.2))
    tc_from_timeseries = convergence_tc_performance(
        pdr_samples=pdr_series,
        der_samples=der_series,
        dt_s=time_bin_s,
        stationary_tail_bins=stationary_tail_bins,
        target_ratio=0.9,
    )

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
        "jain_fairness": jain_fairness(node_successes.values()),
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
        if path.is_dir() and (path / "summary.csv").is_file():
            run_dirs.append(path)
            continue
        if path.is_dir() and (path / "results").is_dir():
            for candidate in sorted((path / "results").iterdir()):
                if candidate.is_dir() and (candidate / "summary.csv").is_file():
                    run_dirs.append(candidate)
    unique = []
    seen = set()
    for item in run_dirs:
        resolved = item.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(item)
    if not unique:
        raise ValueError("Aucun run valide trouvé (summary.csv introuvable).")
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


def aggregate_runs(
    *,
    inputs: Iterable[Path],
    output_root: Path,
    summary_only: bool = False,
    skip_sinr_cdf: bool = False,
    skip_sf_distribution: bool = False,
    strict: bool = False,
    verbose: bool = False,
    ignored_runs_report: list[dict[str, str]] | None = None,
) -> dict[str, Path]:
    """Agrège des runs et écrit les CSV dans ``aggregates/``."""

    run_dirs = _collect_run_dirs(inputs)
    out_dir = output_root / "aggregates"
    out_dir.mkdir(parents=True, exist_ok=True)

    if summary_only:
        skip_sinr_cdf = True
        skip_sf_distribution = True

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

    def _coerce_float(value: Any, *, field: str) -> float:
        try:
            parsed = float(value or 0.0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"valeur non numérique pour '{field}' ({value!r})") from exc
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
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            skipped += 1
            ignored_runs.append(
                {
                    "run_dir": str(run_dir),
                    "reason": "missing_files",
                    "details": ", ".join(sorted(missing_files)),
                }
            )
            continue

        summary_rows = list(_iter_csv(run_dir / "summary.csv"))
        if not summary_rows:
            message = f"Run corrompu ignoré: {run_dir} (summary.csv vide)"
            if strict:
                raise ValueError(message)
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            skipped += 1
            ignored_runs.append({"run_dir": str(run_dir), "reason": "empty_summary", "details": "summary.csv vide"})
            continue

        valid_summary_rows: list[Mapping[str, str]] = []
        parsed_summary_values: list[tuple[tuple[str, ...], dict[str, float]]] = []
        for row in summary_rows:
            try:
                key = tuple(_factor_value(row, column) for column in factor_columns)
                parsed_metrics: dict[str, float] = {}
                for metric_name in metric_names:
                    parsed_metrics[metric_name] = _coerce_float(row.get(metric_name, 0.0), field=metric_name)
            except ValueError as exc:
                message = f"Run corrompu ignoré: {run_dir} ({exc})"
                if strict:
                    raise ValueError(message) from exc
                warnings.warn(message, RuntimeWarning, stacklevel=2)
                skipped += 1
                ignored_runs.append({"run_dir": str(run_dir), "reason": "corrupted_summary", "details": str(exc)})
                valid_summary_rows = []
                parsed_summary_values = []
                break

            convergence_writer.writerow(
                {
                    **{column: row.get(column, "") for column in SCENARIO_ID_COLUMNS},
                    "run_id": row.get("run_id", ""),
                    "Tc_s": row.get("Tc_s", ""),
                }
            )
            fairness_writer.writerow(
                {
                    **{column: row.get(column, "") for column in SCENARIO_ID_COLUMNS},
                    "run_id": row.get("run_id", ""),
                    "jain_fairness": row.get("jain_fairness", ""),
                    "airtime_total_s": row.get("airtime_total_s", ""),
                    "switch_count": row.get("switch_count", ""),
                }
            )
            valid_summary_rows.append(row)
            parsed_summary_values.append((key, parsed_metrics))

        if not valid_summary_rows:
            continue

        for key, parsed_metrics in parsed_summary_values:
            bucket = metric_accumulators[key]
            for metric_name, metric_value in parsed_metrics.items():
                bucket[metric_name].append(metric_value)

        processed += 1

        if summary_only:
            continue

        for row in _iter_csv(run_dir / "events.csv"):
            if row.get("event_type") != "uplink":
                continue
            key = tuple(_factor_value(row, column) for column in factor_columns)
            if not skip_sf_distribution:
                sf_counter[key][row.get("sf", "")] += 1
            if not skip_sinr_cdf:
                sinr_values[key].append(float(row.get("sinr_db", 0.0) or 0.0))

        run_summary = valid_summary_rows[0]
        if run_summary is None:
            continue
        run_algo = str(run_summary.get("algo", "")).lower()
        if run_algo not in {"ucb", "ucb_forget"}:
            continue
        uplinks = [
            row
            for row in _iter_csv(run_dir / "events.csv")
            if row.get("event_type") == "uplink"
        ]
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

    if processed == 0:
        raise ValueError("Aucun run complet à agréger.")

    print(f"Dossiers traités: {processed}/{total}")
    if skipped:
        print(f"Runs incomplets ignorés: {skipped}")

    metric_by_factor_rows = []
    algo_index = factor_columns.index("algo")
    distinct_groups_by_algo: dict[str, int] = {}
    for key, bucket in sorted(metric_accumulators.items()):
        num_runs = len(bucket["pdr"])

        def _mean_and_ci95(values: list[float]) -> tuple[float, float]:
            if not values:
                return 0.0, 0.0
            mean = sum(values) / len(values)
            if len(values) < 2:
                return mean, 0.0
            return mean, 1.96 * stdev(values) / math.sqrt(len(values))

        pdr_mean, pdr_ci95 = _mean_and_ci95(bucket["pdr"])
        der_mean, der_ci95 = _mean_and_ci95(bucket["der"])
        throughput_mean, throughput_ci95 = _mean_and_ci95(bucket["throughput_bps"])
        tc_mean, tc_ci95 = _mean_and_ci95(bucket["Tc_s"])
        jain_mean, jain_ci95 = _mean_and_ci95(bucket["jain_fairness"])
        airtime_mean, airtime_ci95 = _mean_and_ci95(bucket["airtime_total_s"])
        outage_mean, outage_ci95 = _mean_and_ci95(bucket["outage_ratio"])
        switch_mean, switch_ci95 = _mean_and_ci95(bucket["switch_count"])

        metric_by_factor_rows.append(
            {
                **dict(zip(factor_columns, key, strict=False)),
                "sigma": key[-1],
                "n_runs_effective": num_runs,
                "num_runs": num_runs,
                "pdr_mean": pdr_mean,
                "pdr_ci95": pdr_ci95,
                "der_mean": der_mean,
                "der_ci95": der_ci95,
                "throughput_bps_mean": throughput_mean,
                "throughput_bps_ci95": throughput_ci95,
                "Tc_s_mean": tc_mean,
                "Tc_s_ci95": tc_ci95,
                "jain_fairness_mean": jain_mean,
                "jain_fairness_ci95": jain_ci95,
                "airtime_total_s_mean": airtime_mean,
                "airtime_total_s_ci95": airtime_ci95,
                "outage_ratio_mean": outage_mean,
                "outage_ratio_ci95": outage_ci95,
                "switch_count_mean": switch_mean,
                "switch_count_ci95": switch_ci95,
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
        "sigma",
        "n_runs_effective",
        "num_runs",
        "pdr_mean",
        "pdr_ci95",
        "der_mean",
        "der_ci95",
        "throughput_bps_mean",
        "throughput_bps_ci95",
        "Tc_s_mean",
        "Tc_s_ci95",
        "jain_fairness_mean",
        "jain_fairness_ci95",
        "airtime_total_s_mean",
        "airtime_total_s_ci95",
        "outage_ratio_mean",
        "outage_ratio_ci95",
        "switch_count_mean",
        "switch_count_ci95",
    ], metric_by_factor_rows)

    files: dict[str, Path] = {"metric_by_factor": metric_by_factor_path}

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
        for key, values in sorted(sinr_values.items()):
            if not values:
                continue
            factors = dict(zip(factor_columns, key, strict=False))
            data = sorted(values)
            n = len(data)
            quantiles = [index / n for index in range(1, n + 1)]
            _validate_sinr_cdf_group(
                key=key,
                quantiles=quantiles,
                sinrs=data,
                factor_columns=factor_columns,
            )
            for quantile, sinr in zip(quantiles, data, strict=False):
                sinr_rows.append(
                    {
                        **factors,
                        "quantile": quantile,
                        "sinr_db": sinr,
                        "sample_count": n,
                    }
                )
        sinr_path = out_dir / "sinr_cdf.csv"
        _write_csv(sinr_path, factor_columns + ["quantile", "sinr_db", "sample_count"], sinr_rows)
        files["sinr_cdf"] = sinr_path

    files["convergence_tc"] = convergence_path
    files["fairness_airtime_switching"] = fairness_path

    grouped_tracking: dict[tuple[str, str, str], dict[str, float]] = defaultdict(lambda: {
        "num_runs": 0.0,
        "Tc_s_sum": 0.0,
        "regret_proxy_sum": 0.0,
        "exploration_rate_sum": 0.0,
        "decision_stability_sum": 0.0,
    })
    for row in ucb_tracking_rows:
        key = (str(row["speed"]), str(row["mode"]), str(row["algo"]))
        bucket = grouped_tracking[key]
        bucket["num_runs"] += 1.0
        bucket["Tc_s_sum"] += float(row.get("Tc_s", 0.0) or 0.0)
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
                "Tc_s_mean": bucket["Tc_s_sum"] / num_runs,
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
    found_runs = len(run_dirs)

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

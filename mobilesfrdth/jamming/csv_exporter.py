"""Export CSV des résultats de brouillage."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

RUN_SUMMARY_COLUMNS = [
    "scenario",
    "nodes",
    "adr",
    "seed",
    "until_s",
    "legitimate_packet_count",
    "received_packets",
    "lost_packets",
    "jammed_packets",
    "pdr",
    "node_count",
    "jamming_window_count",
    "jamming_windows",
]

PACKET_EVENTS_COLUMNS = [
    "scenario",
    "nodes",
    "adr",
    "seed",
    "packet_id",
    "time_s",
    "node_id",
    "gateway_id",
    "kind",
    "sf",
    "frequency_mhz",
    "channel_id",
    "tx_power_dbm",
    "payload_bytes",
    "airtime_s",
    "sent",
    "received",
    "lost",
    "collided",
    "jammed",
    "delay_s",
]

NODE_METRICS_COLUMNS = [
    "scenario",
    "nodes",
    "adr",
    "seed",
    "node_id",
    "sent",
    "received",
    "lost",
    "collided",
    "jammed",
    "pdr",
    "jammed_ratio",
    "mean_delay_s",
]

CHANNEL_TIMESERIES_COLUMNS = [
    "scenario",
    "nodes",
    "adr",
    "seed",
    "time_s",
    "channel_id",
    "sent",
    "received",
    "lost",
    "jammed",
]

SF_TIMESERIES_COLUMNS = [
    "scenario",
    "nodes",
    "adr",
    "seed",
    "time_s",
    "sf",
    "sent",
    "received",
    "lost",
    "jammed",
]

CAMPAIGN_SUMMARY_COLUMNS = [
    "campaign",
    "scenario",
    "nodes",
    "adr",
    "seed_count",
    "run_count",
    "legitimate_packet_count",
    "received_packets",
    "lost_packets",
    "jammed_packets",
    "pdr_mean",
    "pdr_min",
    "pdr_max",
]

_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def export_jamming_rows(rows: list[Mapping[str, Any]], output_csv: str | Path) -> Path:
    """Écrit des lignes de métriques de brouillage dans un CSV."""

    path = Path(output_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_rows = []
    for row in rows:
        normalized = dict(row)
        if "scenario_name" not in normalized:
            normalized["scenario_name"] = normalized.get(
                "scenario", normalized.get("name", "")
            )
        normalized_rows.append(normalized)

    fieldnames = sorted({key for row in normalized_rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_rows)
    return path


def write_run_csvs(
    result: Any,
    output_layout: str | Path | Mapping[str, Any] | Any,
    export_raw_events: bool = True,
) -> dict[str, Path]:
    """Écrit les CSV d'un run avant toute agrégation de campagne.

    ``output_layout`` peut être le dossier racine de sortie, un mapping, ou un
    objet exposant ``root``/``base_dir``/``raw``/``per_run``. L'arborescence
    produite contient toujours ``raw/`` et ``per_run/``.
    """

    raw_dir, per_run_dir = _resolve_layout(output_layout)
    raw_dir.mkdir(parents=True, exist_ok=True)
    per_run_dir.mkdir(parents=True, exist_ok=True)

    context = _run_context(result)
    suffix = _run_suffix(context)
    written: dict[str, Path] = {}

    run_summary_path = per_run_dir / "run_summary.csv"
    _write_csv(
        run_summary_path,
        RUN_SUMMARY_COLUMNS,
        [_with_context(_as_mapping(getattr(result, "run_summary", {})), context)],
    )
    written["run_summary"] = run_summary_path

    if export_raw_events:
        packet_events_path = raw_dir / f"packet_events_{suffix}.csv"
        _write_csv(
            packet_events_path,
            PACKET_EVENTS_COLUMNS,
            (
                _with_context(event, context)
                for event in getattr(result, "raw_events", [])
            ),
        )
        written["packet_events"] = packet_events_path
    else:
        note_path = raw_dir / f"packet_events_{suffix}.SKIPPED.txt"
        note_path.write_text(
            "packet_events.csv volontairement non exporté car export_raw_events=false. "
            "Les CSV run_summary, node_metrics, channel_timeseries et sf_timeseries restent disponibles.\n",
            encoding="utf-8",
        )
        written["packet_events_note"] = note_path

    node_metrics_path = raw_dir / f"node_metrics_{suffix}.csv"
    _write_csv(
        node_metrics_path, NODE_METRICS_COLUMNS, _node_metric_rows(result, context)
    )
    written["node_metrics"] = node_metrics_path

    channel_timeseries_path = raw_dir / f"channel_timeseries_{suffix}.csv"
    _write_csv(
        channel_timeseries_path,
        CHANNEL_TIMESERIES_COLUMNS,
        _aggregate_timeseries(result, context, "channel_id"),
    )
    written["channel_timeseries"] = channel_timeseries_path

    sf_timeseries_path = raw_dir / f"sf_timeseries_{suffix}.csv"
    _write_csv(
        sf_timeseries_path,
        SF_TIMESERIES_COLUMNS,
        _aggregate_timeseries(result, context, "sf"),
    )
    written["sf_timeseries"] = sf_timeseries_path

    return written


def _resolve_layout(
    output_layout: str | Path | Mapping[str, Any] | Any,
) -> tuple[Path, Path]:
    if isinstance(output_layout, (str, Path)):
        root = Path(output_layout)
        return root / "raw", root / "per_run"

    def get(name: str, default: Any = None) -> Any:
        if isinstance(output_layout, Mapping):
            return output_layout.get(name, default)
        return getattr(output_layout, name, default)

    root = Path(get("root", get("base_dir", get("output_dir", "."))))
    return Path(get("raw", root / "raw")), Path(get("per_run", root / "per_run"))


def _run_context(result: Any) -> dict[str, Any]:
    summary = _as_mapping(getattr(result, "run_summary", {}))
    raw_events = list(getattr(result, "raw_events", []) or [])
    nodes = summary.get("nodes", summary.get("node_count"))
    if nodes in (None, ""):
        nodes = len(getattr(result, "metrics_by_node", {}) or {})
    scenario = summary.get(
        "scenario", summary.get("scenario_name", summary.get("name", "unknown"))
    )
    adr_value = summary.get(
        "adr", summary.get("adr_enabled", summary.get("algo", "unknown"))
    )
    return {
        "scenario": scenario,
        "nodes": nodes,
        "adr": _adr_label(adr_value),
        "seed": summary.get("seed", _first_value(raw_events, "seed", "")),
    }


def _adr_label(value: Any) -> str:
    if isinstance(value, bool):
        return "on" if value else "off"
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on", "adr"}:
        return "on"
    if text in {"false", "0", "no", "n", "off", "noadr", "none"}:
        return "off"
    return text or "unknown"


def _run_suffix(context: Mapping[str, Any]) -> str:
    scenario = _safe_filename(context.get("scenario", "unknown"))
    nodes = _safe_filename(context.get("nodes", "unknown"))
    adr = _safe_filename(context.get("adr", "unknown"))
    seed = _safe_filename(context.get("seed", "unknown"))
    return f"{scenario}_n{nodes}_adr_{adr}_seed_{seed}"


def _safe_filename(value: Any) -> str:
    text = str(value if value not in (None, "") else "unknown")
    return _FILENAME_SAFE_RE.sub("_", text).strip("_") or "unknown"


def _write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[Mapping[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def _with_context(
    row: Mapping[str, Any] | Any, context: Mapping[str, Any]
) -> dict[str, Any]:
    normalized = dict(context)
    normalized.update(_as_mapping(row))
    normalized["scenario"] = normalized.get("scenario") or context.get("scenario")
    normalized["nodes"] = normalized.get("nodes") or context.get("nodes")
    normalized["adr"] = _adr_label(normalized.get("adr", context.get("adr")))
    normalized["seed"] = normalized.get("seed", context.get("seed"))
    return normalized


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}


def _node_metric_rows(
    result: Any, context: Mapping[str, Any]
) -> Iterable[dict[str, Any]]:
    metrics = getattr(result, "metrics_by_node", {}) or {}
    for node_id in sorted(
        metrics, key=lambda item: int(item) if str(item).isdigit() else str(item)
    ):
        row = _with_context(metrics[node_id], context)
        row["node_id"] = node_id
        yield row


def _aggregate_timeseries(
    result: Any, context: Mapping[str, Any], dimension: str
) -> Iterable[dict[str, Any]]:
    buckets: dict[tuple[Any, Any], dict[str, Any]] = {}
    for row in getattr(result, "channel_sf_timeseries", []) or []:
        data = _as_mapping(row)
        key = (data.get("time_s", ""), data.get(dimension, ""))
        bucket = buckets.setdefault(
            key,
            {
                "time_s": key[0],
                dimension: key[1],
                "sent": 0,
                "received": 0,
                "lost": 0,
                "jammed": 0,
            },
        )
        for field_name in ("sent", "received", "lost", "jammed"):
            bucket[field_name] += int(data.get(field_name, 0) or 0)
    for key in sorted(buckets):
        yield _with_context(buckets[key], context)


def _first_value(rows: Iterable[Any], key: str, default: Any = None) -> Any:
    for row in rows:
        data = _as_mapping(row)
        if key in data:
            return data[key]
    return default


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


__all__ = [
    "CAMPAIGN_SUMMARY_COLUMNS",
    "CHANNEL_TIMESERIES_COLUMNS",
    "NODE_METRICS_COLUMNS",
    "PACKET_EVENTS_COLUMNS",
    "RUN_SUMMARY_COLUMNS",
    "SF_TIMESERIES_COLUMNS",
    "export_jamming_rows",
    "write_run_csvs",
]

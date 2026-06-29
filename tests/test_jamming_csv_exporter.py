from __future__ import annotations

import csv
from pathlib import Path

from mobilesfrdth.jamming.csv_exporter import (
    CHANNEL_TIMESERIES_COLUMNS,
    NODE_METRICS_COLUMNS,
    PACKET_EVENTS_COLUMNS,
    RUN_SUMMARY_COLUMNS,
    SF_TIMESERIES_COLUMNS,
    write_run_csvs,
)
from mobilesfrdth.jamming.runner import JammingRunResult


def _header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def test_jamming_run_export_generates_five_csvs_with_expected_columns(tmp_path: Path) -> None:
    result = JammingRunResult(
        raw_events=[
            {
                "packet_id": "pkt-1",
                "time_s": 0.0,
                "node_id": 1,
                "gateway_id": "gw0",
                "kind": "uplink",
                "sf": 7,
                "frequency_mhz": 868.1,
                "channel_id": 0,
                "tx_power_dbm": 14.0,
                "payload_bytes": 12,
                "airtime_s": 0.01,
                "sent": True,
                "received": True,
                "lost": False,
                "collided": False,
                "jammed": False,
                "delay_s": 0.01,
            }
        ],
        metrics_by_node={1: {"sent": 1, "received": 1, "lost": 0, "collided": 0, "jammed": 0, "pdr": 1.0, "jammed_ratio": 0.0, "mean_delay_s": 0.01}},
        channel_sf_timeseries=[{"time_s": 0.0, "channel_id": 0, "sf": 7, "sent": 1, "received": 1, "lost": 0, "jammed": 0}],
        run_summary={"scenario": "smoke", "nodes": 1, "adr": "on", "seed": 0, "until_s": 1.0, "legitimate_packet_count": 1, "received_packets": 1, "lost_packets": 0, "jammed_packets": 0, "pdr": 1.0, "node_count": 1, "jamming_window_count": 0, "jamming_windows": []},
    )

    written = write_run_csvs(result, tmp_path)

    assert set(written) == {"run_summary", "packet_events", "node_metrics", "channel_timeseries", "sf_timeseries"}
    assert _header(written["run_summary"]) == RUN_SUMMARY_COLUMNS
    assert _header(written["packet_events"]) == PACKET_EVENTS_COLUMNS
    assert _header(written["node_metrics"]) == NODE_METRICS_COLUMNS
    assert _header(written["channel_timeseries"]) == CHANNEL_TIMESERIES_COLUMNS
    assert _header(written["sf_timeseries"]) == SF_TIMESERIES_COLUMNS

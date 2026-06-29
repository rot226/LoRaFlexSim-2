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


def _result() -> JammingRunResult:
    return JammingRunResult(
        raw_events=[
            {
                "packet_id": "p1",
                "time_s": 0.0,
                "node_id": 1,
                "gateway_id": "gw0",
                "kind": "uplink",
                "sf": 7,
                "frequency_mhz": 868.1,
                "channel_id": 0,
                "tx_power_dbm": 14.0,
                "payload_bytes": 12,
                "airtime_s": 0.1,
                "sent": True,
                "received": False,
                "lost": True,
                "collided": False,
                "jammed": True,
                "delay_s": 0.1,
            }
        ],
        metrics_by_node={
            1: {
                "sent": 1,
                "received": 0,
                "lost": 1,
                "collided": 0,
                "jammed": 1,
                "pdr": 0.0,
                "jammed_ratio": 1.0,
                "mean_delay_s": 0.1,
            }
        },
        channel_sf_timeseries=[
            {
                "time_s": 0,
                "channel_id": 0,
                "sf": 7,
                "sent": 1,
                "received": 0,
                "lost": 1,
                "jammed": 1,
            }
        ],
        run_summary={
            "scenario": "baseline",
            "node_count": 1,
            "adr": True,
            "seed": 42,
            "until_s": 1.0,
            "legitimate_packet_count": 1,
            "received_packets": 0,
            "lost_packets": 1,
            "jammed_packets": 1,
            "pdr": 0.0,
            "jamming_window_count": 1,
            "jamming_windows": [],
        },
    )


def _header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def test_write_run_csvs_uses_fixed_columns_and_layout(tmp_path: Path) -> None:
    written = write_run_csvs(_result(), tmp_path)
    suffix = "baseline_n1_adr_on_seed_42"

    assert written["packet_events"] == tmp_path / "raw" / f"packet_events_{suffix}.csv"
    assert written["node_metrics"] == tmp_path / "raw" / f"node_metrics_{suffix}.csv"
    assert (
        written["channel_timeseries"]
        == tmp_path / "raw" / f"channel_timeseries_{suffix}.csv"
    )
    assert written["sf_timeseries"] == tmp_path / "raw" / f"sf_timeseries_{suffix}.csv"
    assert written["run_summary"] == tmp_path / "per_run" / "run_summary.csv"

    assert _header(written["run_summary"]) == RUN_SUMMARY_COLUMNS
    assert _header(written["packet_events"]) == PACKET_EVENTS_COLUMNS
    assert _header(written["node_metrics"]) == NODE_METRICS_COLUMNS
    assert _header(written["channel_timeseries"]) == CHANNEL_TIMESERIES_COLUMNS
    assert _header(written["sf_timeseries"]) == SF_TIMESERIES_COLUMNS


def test_write_run_csvs_can_skip_packet_events_with_note(tmp_path: Path) -> None:
    written = write_run_csvs(_result(), tmp_path, export_raw_events=False)

    assert "packet_events" not in written
    note = written["packet_events_note"]
    assert note.name == "packet_events_baseline_n1_adr_on_seed_42.SKIPPED.txt"
    assert "volontairement non exporté" in note.read_text(encoding="utf-8")
    assert written["run_summary"].exists()
    assert written["node_metrics"].exists()
    assert written["channel_timeseries"].exists()
    assert written["sf_timeseries"].exists()

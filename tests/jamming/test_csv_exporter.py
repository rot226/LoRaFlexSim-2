import csv
from pathlib import Path

from mobilesfrdth.jamming.aggregate import aggregate_existing_results
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


def test_aggregate_existing_results_groups_runs_and_writes_ci95(tmp_path: Path) -> None:
    run1 = tmp_path / "run1" / "per_run"
    run2 = tmp_path / "run2" / "per_run"
    run1.mkdir(parents=True)
    run2.mkdir(parents=True)
    header = [
        "scenario",
        "node_count",
        "adr",
        "channel_selection",
        "seed",
        "pdr",
        "lost_packets",
        "jammed_packets",
        "mean_delay_s",
        "collided_packets",
        "channel_changes",
        "sf_changes",
    ]
    for path, seed, pdr, lost in [
        (run1 / "run_summary.csv", 1, 0.8, 2),
        (run2 / "run_summary.csv", 2, 1.0, 0),
    ]:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerow(
                {
                    "scenario": "baseline",
                    "node_count": "20",
                    "adr": "True",
                    "channel_selection": "static",
                    "seed": seed,
                    "pdr": pdr,
                    "lost_packets": lost,
                    "jammed_packets": 1,
                    "mean_delay_s": 0.1,
                    "collided_packets": 3,
                    "channel_changes": 4,
                    "sf_changes": 5,
                }
            )

    output = aggregate_existing_results(
        tmp_path, tmp_path / "aggregate" / "campaign_summary.csv"
    )

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    row = rows[0]
    assert row["scenario_name"] == "baseline"
    assert row["node_count"] == "20"
    assert row["adr_enabled"] == "true"
    assert row["channel_selection"] == "static"
    assert row["seeds_count"] == "2"
    assert row["pdr_mean"] == "0.9"
    assert row["pdr_ci95_half_width"] != ""
    assert row["lost_packets_mean"] == "1"
    assert row["jammed_packets_mean"] == "1"
    assert row["mean_delay_s_mean"] == "0.1"
    assert row["collided_packets_mean"] == "3"
    assert row["channel_changes_mean"] == "4"
    assert row["sf_changes_mean"] == "5"

import json

import pytest

from mobilesfrdth.jamming.campaigns import run_campaign
from mobilesfrdth.jamming.scenarios import JammingScenario


class DummyResult:
    def __init__(self):
        self.run_summary = {}


def test_run_campaign_writes_campaign_and_run_logs(tmp_path, monkeypatch):
    def fake_run_jamming_simulation(**kwargs):
        assert kwargs["seed"] == 7
        return DummyResult()

    def fake_write_run_csvs(result, layout):
        written = {
            "run_summary": layout["per_run"] / "run_summary.csv",
            "node_metrics": layout["raw"] / "node_metrics_7.csv",
        }
        for path in written.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("ok\n", encoding="utf-8")
        return written

    monkeypatch.setattr(
        "mobilesfrdth.jamming.campaigns.run_jamming_simulation",
        fake_run_jamming_simulation,
    )
    monkeypatch.setattr(
        "mobilesfrdth.jamming.campaigns.write_run_csvs", fake_write_run_csvs
    )
    monkeypatch.setattr(
        "mobilesfrdth.jamming.campaigns.aggregate_existing_results",
        lambda *_args, **_kwargs: None,
    )

    run_campaign(
        layout=tmp_path,
        scenarios=[JammingScenario(name="Test Scenario", metadata={"sim_time_s": 12})],
        node_counts=[3],
        seeds=[7],
        adr_modes=[True],
        channel_selections=["static"],
    )

    campaign_log = tmp_path / "logs" / "campaign.log"
    run_log = tmp_path / "logs" / "run_test_scenario_n3_adr_on_seed_7.log"
    assert campaign_log.is_file()
    assert run_log.is_file()
    run_events = [
        json.loads(line) for line in run_log.read_text(encoding="utf-8").splitlines()
    ]
    assert run_events[0]["parameters"]["sim_time_s"] == 12.0
    assert run_events[0]["seed"] == 7
    assert run_events[-1]["status"] == "completed"
    assert "run_summary" in run_events[-1]["csv"]


def test_run_campaign_marks_failed_status_before_reraising(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "mobilesfrdth.jamming.campaigns.run_jamming_simulation",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(RuntimeError, match="boom"):
        run_campaign(
            layout=tmp_path,
            scenarios=[JammingScenario(name="Failing", metadata={"sim_time_s": 1})],
            node_counts=[1],
            seeds=[4],
            adr_modes=[False],
            channel_selections=["static"],
        )

    status_path = (
        tmp_path / "runs" / "failing_n1_adr_off_seed_4_ch_static" / "status.json"
    )
    assert json.loads(status_path.read_text(encoding="utf-8"))["status"] == "failed"
    run_log = tmp_path / "logs" / "run_failing_n1_adr_off_seed_4.log"
    assert '"status": "failed"' in run_log.read_text(encoding="utf-8")


def test_run_campaign_writes_final_aggregate_after_non_skipped_runs(
    tmp_path, monkeypatch
):
    from mobilesfrdth.jamming.runner import JammingRunResult

    def fake_run_jamming_simulation(**kwargs):
        seed = kwargs["seed"]
        return JammingRunResult(
            raw_events=[],
            metrics_by_node={
                1: {
                    "sent": 1,
                    "received": 1,
                    "lost": 0,
                    "collided": 0,
                    "jammed": 0,
                    "pdr": 1.0,
                    "jammed_ratio": 0.0,
                    "mean_delay_s": 0.0,
                }
            },
            channel_sf_timeseries=[
                {
                    "time_s": 0.0,
                    "channel_id": 0,
                    "sf": 7,
                    "sent": 1,
                    "received": 1,
                    "lost": 0,
                    "jammed": 0,
                }
            ],
            run_summary={
                "until_s": 1.0,
                "legitimate_packet_count": 1,
                "received_packets": 1,
                "lost_packets": 0,
                "jammed_packets": 0,
                "pdr": 1.0,
                "node_count": 1,
                "jamming_window_count": 0,
                "jamming_windows": [],
                "seed": seed,
            },
        )

    monkeypatch.setattr(
        "mobilesfrdth.jamming.campaigns.run_jamming_simulation",
        fake_run_jamming_simulation,
    )

    run_campaign(
        layout=tmp_path,
        scenarios=[JammingScenario(name="Mini", metadata={"sim_time_s": 1})],
        node_counts=[1],
        seeds=[10, 11],
        adr_modes=[False],
        channel_selections=["static"],
    )

    summary = tmp_path / "aggregate" / "campaign_summary.csv"
    assert summary.is_file()
    text = summary.read_text(encoding="utf-8")
    assert "seeds_count" in text
    assert "2" in text


def test_completed_campaign_runs_keep_raw_csvs_and_run_summary(tmp_path, monkeypatch):
    from mobilesfrdth.jamming.runner import JammingRunResult

    def fake_run_jamming_simulation(**kwargs):
        seed = kwargs["seed"]
        return JammingRunResult(
            raw_events=[
                {
                    "packet_id": f"p{seed}",
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
                    "received": True,
                    "lost": False,
                    "collided": False,
                    "jammed": False,
                    "delay_s": 0.1,
                }
            ],
            metrics_by_node={
                1: {
                    "sent": 1,
                    "received": 1,
                    "lost": 0,
                    "collided": 0,
                    "jammed": 0,
                    "pdr": 1.0,
                    "jammed_ratio": 0.0,
                    "mean_delay_s": 0.1,
                }
            },
            channel_sf_timeseries=[
                {
                    "time_s": 0.0,
                    "channel_id": 0,
                    "sf": 7,
                    "sent": 1,
                    "received": 1,
                    "lost": 0,
                    "jammed": 0,
                }
            ],
            run_summary={
                "until_s": 1.0,
                "legitimate_packet_count": 1,
                "received_packets": 1,
                "lost_packets": 0,
                "jammed_packets": 0,
                "pdr": 1.0,
                "node_count": 1,
                "jamming_window_count": 0,
                "jamming_windows": [],
                "seed": seed,
            },
        )

    monkeypatch.setattr(
        "mobilesfrdth.jamming.campaigns.run_jamming_simulation",
        fake_run_jamming_simulation,
    )

    runs = run_campaign(
        layout=tmp_path,
        scenarios=[JammingScenario(name="Raw Check", metadata={"sim_time_s": 1})],
        node_counts=[1],
        seeds=[20, 21],
        adr_modes=[True],
        channel_selections=["static"],
    )

    for run_key in runs:
        run_dir = tmp_path / "runs" / run_key.run_id
        assert (run_dir / "per_run" / "run_summary.csv").is_file()
        assert list((run_dir / "raw").glob("packet_events_*.csv"))
        assert list((run_dir / "raw").glob("node_metrics_*.csv"))
        assert list((run_dir / "raw").glob("channel_timeseries_*.csv"))
        assert list((run_dir / "raw").glob("sf_timeseries_*.csv"))

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

    monkeypatch.setattr("mobilesfrdth.jamming.campaigns.run_jamming_simulation", fake_run_jamming_simulation)
    monkeypatch.setattr("mobilesfrdth.jamming.campaigns.write_run_csvs", fake_write_run_csvs)
    monkeypatch.setattr("mobilesfrdth.jamming.campaigns.aggregate_existing_results", lambda *_args, **_kwargs: None)

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
    run_events = [json.loads(line) for line in run_log.read_text(encoding="utf-8").splitlines()]
    assert run_events[0]["parameters"]["sim_time_s"] == 12.0
    assert run_events[0]["seed"] == 7
    assert run_events[-1]["status"] == "completed"
    assert "run_summary" in run_events[-1]["csv"]


def test_run_campaign_marks_failed_status_before_reraising(tmp_path, monkeypatch):
    monkeypatch.setattr("mobilesfrdth.jamming.campaigns.run_jamming_simulation", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(RuntimeError, match="boom"):
        run_campaign(
            layout=tmp_path,
            scenarios=[JammingScenario(name="Failing", metadata={"sim_time_s": 1})],
            node_counts=[1],
            seeds=[4],
            adr_modes=[False],
            channel_selections=["static"],
        )

    status_path = tmp_path / "runs" / "failing_n1_adr_off_seed_4_ch_static" / "status.json"
    assert json.loads(status_path.read_text(encoding="utf-8"))["status"] == "failed"
    run_log = tmp_path / "logs" / "run_failing_n1_adr_off_seed_4.log"
    assert '"status": "failed"' in run_log.read_text(encoding="utf-8")

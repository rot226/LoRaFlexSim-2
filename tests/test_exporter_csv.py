import json
import subprocess
import pytest

try:
    pn = pytest.importorskip("panel")
    pd = pytest.importorskip("pandas")
except Exception:
    pytest.skip("panel or pandas import failed", allow_module_level=True)

from loraflexsim.launcher import dashboard  # noqa: E402


def test_export_to_tmp_dir(tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            "start_time": [0.0, 1.0],
            "node_id": [0, 1],
            "sf": [7, 12],
            "result": ["Success", "CollisionLoss"],
        }
    )
    dashboard.runs_events = [df]
    dashboard.runs_metrics = [{"PDR": 100, "energy_J": 12.5}]
    dashboard.runs_configs = [{"run": 1, "radio": {"snir_mode": True}}]
    dashboard.sim = type("S", (), {"payload_size_bytes": 20})()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)
    dashboard.exporter_csv()
    raw_packets = tmp_path / "raw_packets.csv"
    raw_energy = tmp_path / "raw_energy.csv"
    assert raw_packets.exists()
    assert raw_energy.exists()

    packets_df = pd.read_csv(raw_packets)
    assert list(packets_df.columns)[:6] == [
        "time",
        "node_id",
        "sf",
        "tx_ok",
        "rx_ok",
        "payload_bytes",
    ]
    assert packets_df["sf"].between(7, 12).all()

    energy_df = pd.read_csv(raw_energy)
    assert list(energy_df.columns) == ["run", "total_energy_joule", "sim_duration_s"]

    run_config = tmp_path / "run_1_config.json"
    assert run_config.exists()
    payload = json.loads(run_config.read_text(encoding="utf-8"))
    assert payload["radio"]["snir_mode"] is True


def test_export_raw_energy_keeps_multiple_runs_identifiable(tmp_path, monkeypatch):
    run_1_df = pd.DataFrame(
        {
            "start_time": [0.0, 10.0],
            "node_id": [0, 1],
            "sf": [7, 8],
            "result": ["Success", "Success"],
            "run": [1, 1],
        }
    )
    run_2_df = pd.DataFrame(
        {
            "start_time": [0.0, 20.0],
            "node_id": [0, 1],
            "sf": [9, 10],
            "result": ["Success", "CollisionLoss"],
            "run": [2, 2],
        }
    )
    dashboard.runs_events = [run_1_df, run_2_df]
    dashboard.runs_metrics = [
        {"run": 1, "energy_J": 12.5},
        {"run": 2, "energy_J": 25.0},
    ]
    dashboard.runs_configs = []
    dashboard.sim = type("S", (), {"payload_size_bytes": 20})()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)

    dashboard.exporter_csv()

    energy_df = pd.read_csv(tmp_path / "raw_energy.csv")
    assert list(energy_df.columns) == ["run", "total_energy_joule", "sim_duration_s"]
    assert len(energy_df) == 2
    assert energy_df["run"].tolist() == [1, 2]
    assert energy_df.set_index("run")["total_energy_joule"].to_dict() == {
        1: 12.5,
        2: 25.0,
    }
    assert energy_df.set_index("run")["sim_duration_s"].to_dict() == {1: 10.0, 2: 20.0}

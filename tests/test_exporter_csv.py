import json
import subprocess
import pytest

try:
    pn = pytest.importorskip("panel")
    pd = pytest.importorskip("pandas")
except Exception:
    pytest.skip("panel or pandas import failed", allow_module_level=True)

from loraflexsim.launcher import dashboard  # noqa: E402


def _read_exported_csv(path):
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    return pd.read_csv(path)


def _export_dir(tmp_path):
    exports_root = tmp_path / "results" / "dashboard_exports"
    export_dirs = [path for path in exports_root.iterdir() if path.is_dir()]
    assert len(export_dirs) == 1
    return export_dirs[0]


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
    dashboard.runs_metrics = [
        {
            "PDR": 100,
            "energy_J": 12.5,
            "energy_nodes_J": 8.0,
            "energy_gateways_J": 4.5,
            "simulation_duration_s": 1.0,
        }
    ]
    dashboard.runs_configs = [{"run": 1, "radio": {"snir_mode": True}}]
    dashboard.sim = type("S", (), {"payload_size_bytes": 20})()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)
    dashboard.exporter_csv()
    export_dir = _export_dir(tmp_path)
    raw_packets = export_dir / "raw_packets.csv"
    raw_energy = export_dir / "raw_energy.csv"
    energy_summary = export_dir / "energy_summary.csv"
    assert raw_packets.exists()
    assert raw_energy.exists()
    assert energy_summary.exists()

    packets_df = _read_exported_csv(raw_packets)
    assert list(packets_df.columns)[:6] == [
        "time",
        "node_id",
        "sf",
        "tx_ok",
        "rx_ok",
        "payload_bytes",
    ]
    assert packets_df["sf"].between(7, 12).all()
    assert packets_df["payload_bytes"].tolist() == [20, 20]

    energy_df = _read_exported_csv(raw_energy)
    assert list(energy_df.columns) == ["run", "total_energy_joule", "sim_duration_s"]

    energy_summary_df = _read_exported_csv(energy_summary)
    assert list(energy_summary_df.columns) == [
        "run",
        "total_energy_joule",
        "energy_nodes_joule",
        "energy_gateways_joule",
        "sim_duration_s",
    ]
    assert energy_summary_df.loc[0, "total_energy_joule"] == 12.5
    assert energy_summary_df.loc[0, "energy_nodes_joule"] == 8.0
    assert energy_summary_df.loc[0, "energy_gateways_joule"] == 4.5
    assert energy_summary_df.loc[0, "sim_duration_s"] == 1.0

    run_config = export_dir / "run_1_config.json"
    assert run_config.exists()
    payload = json.loads(run_config.read_text(encoding="utf-8"))
    assert payload["radio"]["snir_mode"] is True


def test_collect_current_run_results_is_idempotent_for_export(tmp_path, monkeypatch):
    class FakeSim:
        payload_size_bytes = 20
        run_config = {"run": 1, "traffic": {"payload_size_bytes": 20}}

        def get_events_dataframe(self):
            return pd.DataFrame(
                {
                    "start_time": [0.0, 1.0],
                    "node_id": [0, 1],
                    "sf": [7, 8],
                    "result": ["Success", "Success"],
                }
            )

        def get_metrics(self):
            return {"PDR": 100.0, "energy_J": 12.5}

    dashboard.runs_events = []
    dashboard.runs_metrics = []
    dashboard.runs_configs = []
    dashboard.current_run = 1
    dashboard.sim = FakeSim()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)

    dashboard._collect_current_run_results()
    dashboard._collect_current_run_results()

    assert len(dashboard.runs_events) == 1
    assert len(dashboard.runs_metrics) == 1
    assert len(dashboard.runs_configs) == 1
    assert dashboard.runs_metrics[0]["run"] == 1
    assert dashboard.runs_configs[0]["run"] == 1

    dashboard.exporter_csv()

    export_dir = _export_dir(tmp_path)
    assert _read_exported_csv(export_dir / "metrics_complete.csv")["run"].tolist() == [
        1
    ]
    assert _read_exported_csv(export_dir / "raw_packets.csv")[
        "run"
    ].unique().tolist() == [1]
    assert _read_exported_csv(export_dir / "runs_config.csv")["run"].tolist() == [1]


def test_export_energy_summary_keeps_multiple_runs_identifiable(tmp_path, monkeypatch):
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
        {
            "run": 1,
            "energy_J": 12.5,
            "energy_nodes_J": 8.0,
            "energy_gateways_J": 4.5,
        },
        {
            "run": 2,
            "energy_J": 25.0,
            "energy_nodes_J": 16.0,
            "energy_gateways_J": 9.0,
        },
    ]
    dashboard.runs_configs = []
    dashboard.sim = type("S", (), {"payload_size_bytes": 20})()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)

    dashboard.exporter_csv()

    export_dir = _export_dir(tmp_path)
    energy_df = _read_exported_csv(export_dir / "energy_summary.csv")
    assert list(energy_df.columns) == [
        "run",
        "total_energy_joule",
        "energy_nodes_joule",
        "energy_gateways_joule",
        "sim_duration_s",
    ]
    assert len(energy_df) == 2
    assert energy_df["run"].tolist() == [1, 2]
    energy_by_run = energy_df.set_index("run")
    assert energy_by_run["total_energy_joule"].to_dict() == {1: 12.5, 2: 25.0}
    assert energy_by_run["energy_nodes_joule"].to_dict() == {1: 8.0, 2: 16.0}
    assert energy_by_run["energy_gateways_joule"].to_dict() == {1: 4.5, 2: 9.0}
    assert energy_by_run["sim_duration_s"].to_dict() == {1: 10.0, 2: 20.0}


def test_export_raw_packets_payload_uses_run_config(tmp_path, monkeypatch):
    run_1_df = pd.DataFrame(
        {
            "start_time": [0.0, 1.0],
            "node_id": [0, 1],
            "sf": [7, 8],
            "result": ["Success", "Success"],
            "run": [1, 1],
        }
    )
    run_2_df = pd.DataFrame(
        {
            "start_time": [0.0, 1.0],
            "node_id": [0, 1],
            "sf": [9, 10],
            "result": ["Success", "CollisionLoss"],
            "run": [2, 2],
        }
    )
    dashboard.runs_events = [run_1_df, run_2_df]
    dashboard.runs_metrics = []
    dashboard.runs_configs = [
        {"run": 1, "traffic": {"payload_size_bytes": 12}},
        {"run": 2, "traffic": {"payload_size_bytes": 34}},
    ]
    dashboard.sim = type("S", (), {"payload_size_bytes": 99})()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)

    dashboard.exporter_csv()

    export_dir = _export_dir(tmp_path)
    packets_df = _read_exported_csv(export_dir / "raw_packets.csv")
    assert packets_df.groupby("run")["payload_bytes"].unique().apply(
        list
    ).to_dict() == {
        1: [12],
        2: [34],
    }


def test_export_writes_complete_multi_run_csv_and_configs(tmp_path, monkeypatch):
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
        {"run": 1, "PDR": 100.0, "energy_J": 12.5},
        {"run": 2, "PDR": 50.0, "energy_J": 25.0},
    ]
    dashboard.runs_configs = [
        {
            "run": 1,
            "seed": 101,
            "traffic": {"payload_size_bytes": 12},
            "radio": {"snir_mode": True},
        },
        {
            "run": 2,
            "seed": 202,
            "traffic": {"payload_size_bytes": 34},
            "radio": {"snir_mode": False},
        },
    ]
    dashboard.sim = type("S", (), {"payload_size_bytes": 99})()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)

    dashboard.exporter_csv()

    export_dir = _export_dir(tmp_path)
    metrics_complete = export_dir / "metrics_complete.csv"
    energy_summary = export_dir / "energy_summary.csv"
    raw_energy = export_dir / "raw_energy.csv"
    raw_packets = export_dir / "raw_packets.csv"

    assert metrics_complete.exists()
    metrics_df = _read_exported_csv(metrics_complete)
    assert len(metrics_df) == 2
    assert metrics_df["run"].tolist() == [1, 2]

    energy_summary_df = _read_exported_csv(energy_summary)
    assert "run" in energy_summary_df.columns

    raw_energy_df = _read_exported_csv(raw_energy)
    assert "run" in raw_energy_df.columns

    raw_packets_df = _read_exported_csv(raw_packets)
    assert sorted(raw_packets_df["run"].unique().tolist()) == [1, 2]

    assert (export_dir / "run_1_config.json").exists()
    assert (export_dir / "run_2_config.json").exists()
    assert (export_dir / "runs_config.csv").exists()


def test_export_writes_node_and_gateway_metrics(tmp_path, monkeypatch):
    dashboard.runs_events = []
    dashboard.runs_metrics = [
        {
            "run": 1,
            "pdr_by_node": {0: 100.0, 1: 50.0},
            "recent_pdr_by_node": {0: 95.0, 1: 45.0},
            "energy_by_node": {0: 1.25, 1: 2.5},
            "airtime_by_node": {0: 0.5, 1: 0.75},
            "energy_breakdown_by_node": {
                0: {"tx": 0.5, "rx": 0.25, "sleep": 0.4, "listen": 0.1},
                1: {"tx": 1.0, "rx": 0.5, "sleep": 0.8, "listen": 0.2},
            },
            "pdr_by_gateway": {"gw-1": 100.0, "gw-2": 75.0},
            "energy_by_gateway": {"gw-1": 3.5, "gw-2": 4.5},
            "energy_breakdown_by_gateway": {
                "gw-1": {"tx": 1.5, "rx": 1.0, "sleep": 0.75, "listen": 0.25},
                "gw-2": {"tx": 2.0, "rx": 1.25, "sleep": 1.0, "listen": 0.25},
            },
        }
    ]
    dashboard.runs_configs = []
    dashboard.sim = type("S", (), {"payload_size_bytes": 20})()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)

    dashboard.exporter_csv()

    export_dir = _export_dir(tmp_path)
    nodes_metrics = export_dir / "nodes_metrics.csv"
    gateways_metrics = export_dir / "gateways_metrics.csv"

    assert nodes_metrics.exists()
    nodes_df = _read_exported_csv(nodes_metrics)
    assert len(nodes_df) == 2
    assert {"run", "node_id", "pdr", "energy_j"}.issubset(nodes_df.columns)

    assert gateways_metrics.exists()
    gateways_df = _read_exported_csv(gateways_metrics)
    assert len(gateways_df) == 2
    assert {"run", "gateway_id", "pdr", "energy_j"}.issubset(gateways_df.columns)


def test_export_writes_qos_clusters_metrics(tmp_path, monkeypatch):
    dashboard.runs_events = []
    dashboard.runs_metrics = [
        {
            "run": 3,
            "qos_cluster_pdr": {1: 95.0, 2: 82.5},
            "qos_cluster_targets": {1: 90.0, 2: 85.0},
            "qos_cluster_pdr_gap": {1: 5.0, 2: -2.5},
            "qos_cluster_throughput_bps": {1: 1200.0, 2: 800.0},
            "qos_cluster_node_counts": {1: 4, 2: 3},
            "qos_cluster_sf_channel": {1: {"sf": 7, "channel": 0}},
            "qos_throughput_gini": 0.25,
        }
    ]
    dashboard.runs_configs = []
    dashboard.sim = type("S", (), {"payload_size_bytes": 20})()
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)

    dashboard.exporter_csv()

    export_dir = _export_dir(tmp_path)
    qos_clusters_metrics = export_dir / "qos_clusters_metrics.csv"
    assert qos_clusters_metrics.exists()

    qos_clusters_df = _read_exported_csv(qos_clusters_metrics)
    assert {
        "run",
        "cluster_id",
        "pdr",
        "pdr_target",
        "pdr_gap",
        "throughput_bps",
        "node_count",
    }.issubset(qos_clusters_df.columns)

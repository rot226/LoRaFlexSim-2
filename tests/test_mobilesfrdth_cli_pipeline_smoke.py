from __future__ import annotations

import csv
import json
import pathlib
from types import SimpleNamespace

from mobilesfrdth import cli


_NON_BONUS_FIGURES = {
    "fig01_pdr_vs_n_snir_off.png",
    "fig02_pdr_vs_n_snir_on.png",
    "fig03_der_vs_n_snir_off.png",
    "fig04_der_vs_n_snir_on.png",
    "fig05_throughput_vs_n_snir_off.png",
    "fig06_throughput_vs_n_snir_on.png",
    "fig07_tc_vs_speed.png",
    "fig08_fairness_vs_n.png",
    "fig09_sf_distribution_snir_on.png",
    "fig10_sinr_cdf.png",
}


def _write_csv(path: pathlib.Path, fieldnames: list[str], row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


def test_cli_smoke_grid_pipeline_contracts_and_run_id_uniqueness(monkeypatch, tmp_path: pathlib.Path) -> None:
    config_path = pathlib.Path(__file__).resolve().parents[1] / "experiments" / "default.yaml"
    runs_dir = tmp_path / "runs"
    aggregates_dir = tmp_path / "aggregates"
    figures_dir = tmp_path / "figures"

    class _FakeOrchestrator:
        def __init__(self, *, output_root: pathlib.Path):
            self.output_root = pathlib.Path(output_root)

        def execute_jobs(self, jobs, **kwargs):
            reports = []
            on_run_complete = kwargs.get("on_run_complete")
            total = len(jobs)
            success_count = 0

            for index, job in enumerate(jobs, start=1):
                params = job["params"]
                run_id = str(params["run_id"])
                run_dir = self.output_root / "results" / run_id
                summary_row = {
                    "N": params["N"],
                    "speed": params["speed"],
                    "mobility_model": str(params.get("model", "RWP")).lower(),
                    "mode": str(params["mode"]).lower(),
                    "algo": str(params["algo"]).lower(),
                    "gateways": 1,
                    "sigma": 0.0,
                    "seed": params["seed"],
                    "rep": params["rep"],
                    "run_id": run_id,
                    "duration_s": 10.0,
                    "node_count": params["N"],
                    "tx_count": 100,
                    "success_count": 80,
                    "generated_packets": 100,
                    "delivered_bytes": 1600,
                    "pdr": 0.8,
                    "der": 0.8,
                    "throughput_bps": 1280.0,
                    "Tc_s": 42.0,
                    "jain_fairness": 0.95,
                    "airtime_total_s": 12.0,
                    "airtime_mean_per_node_s": 0.24,
                    "outage_ratio": 0.01,
                    "switch_count": 2,
                }
                event_row = {
                    "N": params["N"],
                    "speed": params["speed"],
                    "mobility_model": str(params.get("model", "RWP")).lower(),
                    "mode": str(params["mode"]).lower(),
                    "algo": str(params["algo"]).lower(),
                    "gateways": 1,
                    "sigma": 0.0,
                    "seed": params["seed"],
                    "rep": params["rep"],
                    "run_id": run_id,
                    "event_idx": 1,
                    "time_s": 1.0,
                    "event_type": "uplink",
                    "node_id": 0,
                    "sf": 7,
                    "sinr_db": 3.5,
                    "success": 1,
                    "delivered": 1,
                    "payload_bytes": 20,
                    "airtime_s": 0.12,
                    "outage": 0,
                    "switch_count": 0,
                }
                _write_csv(run_dir / "summary.csv", list(summary_row.keys()), summary_row)
                _write_csv(run_dir / "events.csv", list(event_row.keys()), event_row)

                report = SimpleNamespace(run_id=run_id, success=True, run_dir=run_dir, error=None)
                reports.append(report)
                success_count += 1
                if on_run_complete is not None:
                    on_run_complete(report, index, total, success_count, 0, 0.0)

            return SimpleNamespace(
                reports=reports,
                total_jobs=total,
                skipped_runs=0,
                scheduled_runs=total,
                failed_reports=[],
                interrupted=False,
            )

    monkeypatch.setattr("mobilesfrdth.simulator.engine.GridRunOrchestrator", _FakeOrchestrator)

    grid = "N=50;speed=1,5;mode=SNIR_OFF,SNIR_ON;algo=ADR;reps=2;seed_base=123"
    assert cli.main(["run", "--config", str(config_path), "--out", str(runs_dir), "--grid", grid]) == 0

    jobs_payload = json.loads((runs_dir / "jobs.json").read_text(encoding="utf-8"))
    num_jobs = int(jobs_payload["num_jobs"])
    assert num_jobs == 8

    run_ids = [str(job["params"]["run_id"]) for job in jobs_payload["jobs"]]
    assert len(run_ids) == len(set(run_ids)), "Collision run_id détectée dans jobs.json"

    result_run_dirs = [path for path in (runs_dir / "results").iterdir() if path.is_dir()]
    assert len(result_run_dirs) == num_jobs, "Le nombre de dossiers results/<run_id> doit égaler num_jobs de jobs.json"

    assert cli.main(["aggregate", "--results", str(runs_dir), "--out", str(aggregates_dir)]) == 0

    aggregate_manifest = json.loads((aggregates_dir / "aggregate.json").read_text(encoding="utf-8"))
    assert aggregate_manifest["distinct_groups_by_algo"] == {"adr": 4}
    assert aggregate_manifest["ignored_runs"] == []
    assert aggregate_manifest["n_runs_effective"] == num_jobs

    metric_rows = list(
        csv.DictReader((aggregates_dir / "aggregates" / "metric_by_factor.csv").open("r", encoding="utf-8", newline=""))
    )
    aggregated_num_runs = sum(int(float(row["num_runs"])) for row in metric_rows)
    assert aggregated_num_runs == num_jobs

    assert cli.main(
        [
            "plots",
            "--aggregates-dir",
            str(aggregates_dir / "aggregates"),
            "--out",
            str(figures_dir),
        ]
    ) == 0

    plots_payload = json.loads((figures_dir / "plots_summary.json").read_text(encoding="utf-8"))
    generated_figure_names = {pathlib.Path(path).name for path in plots_payload["figures"]}
    expected_figures = _NON_BONUS_FIGURES - {"fig10_sinr_cdf.png"}
    assert expected_figures.issubset(generated_figure_names)
    assert plots_payload["article_profile"] == "core"
    fig02_filters = {
        entry["figure"]: entry["filters"] for entry in plots_payload["figure_filters"]
    }["fig02_pdr_vs_n_snir_on.png"]
    assert fig02_filters["mode"] == ["snir_on"]

    fig02_trace = {
        entry["figure"]: entry for entry in plots_payload["figure_filters"]
    }["fig02_pdr_vs_n_snir_on.png"]
    assert "points_by_curve" in fig02_trace

    campaign_log = tmp_path / "campaign_log.jsonl"
    assert campaign_log.is_file()
    campaign_entries = [
        json.loads(line)
        for line in campaign_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [entry["step"] for entry in campaign_entries] == ["run", "aggregate", "plots"]


def test_cli_plots_generates_fig01_to_fig06_with_non_empty_core_campaign(monkeypatch, tmp_path: pathlib.Path) -> None:
    config_path = pathlib.Path(__file__).resolve().parents[1] / "experiments" / "default.yaml"
    runs_dir = tmp_path / "runs_core"
    aggregates_dir = tmp_path / "aggregates_core"
    figures_dir = tmp_path / "figures_core"

    class _FakeOrchestrator:
        def __init__(self, *, output_root: pathlib.Path):
            self.output_root = pathlib.Path(output_root)

        def execute_jobs(self, jobs, **kwargs):
            reports = []
            for job in jobs:
                params = job["params"]
                run_id = str(params["run_id"])
                run_dir = self.output_root / "results" / run_id
                summary_row = {
                    "N": params["N"],
                    "speed": params["speed"],
                    "mobility_model": str(params.get("model", "RWP")).lower(),
                    "mode": str(params["mode"]),
                    "algo": str(params["algo"]),
                    "gateways": 1,
                    "sigma": 0.0,
                    "seed": params["seed"],
                    "rep": params["rep"],
                    "run_id": run_id,
                    "duration_s": 10.0,
                    "node_count": params["N"],
                    "tx_count": 100,
                    "success_count": 80,
                    "generated_packets": 100,
                    "delivered_bytes": 1600,
                    "pdr": 0.8,
                    "der": 0.8,
                    "throughput_bps": 1280.0,
                    "Tc_s": 42.0,
                    "jain_fairness": 0.95,
                    "airtime_total_s": 12.0,
                    "airtime_mean_per_node_s": 0.24,
                    "outage_ratio": 0.01,
                    "switch_count": 2,
                }
                event_row = {
                    "N": params["N"],
                    "speed": params["speed"],
                    "mobility_model": str(params.get("model", "RWP")).lower(),
                    "mode": str(params["mode"]),
                    "algo": str(params["algo"]),
                    "gateways": 1,
                    "sigma": 0.0,
                    "seed": params["seed"],
                    "rep": params["rep"],
                    "run_id": run_id,
                    "event_idx": 1,
                    "time_s": 1.0,
                    "event_type": "uplink",
                    "node_id": 0,
                    "sf": 7,
                    "sinr_db": 3.5,
                    "success": 1,
                    "delivered": 1,
                    "payload_bytes": 20,
                    "airtime_s": 0.12,
                    "outage": 0,
                    "switch_count": 0,
                }
                _write_csv(run_dir / "summary.csv", list(summary_row.keys()), summary_row)
                _write_csv(run_dir / "events.csv", list(event_row.keys()), event_row)
                reports.append(SimpleNamespace(run_id=run_id, success=True, run_dir=run_dir, error=None))

            total = len(jobs)
            return SimpleNamespace(
                reports=reports,
                total_jobs=total,
                skipped_runs=0,
                scheduled_runs=total,
                failed_reports=[],
                interrupted=False,
            )

    monkeypatch.setattr("mobilesfrdth.simulator.engine.GridRunOrchestrator", _FakeOrchestrator)

    assert cli.main(["run", "--config", str(config_path), "--out", str(runs_dir), "--profile", "core"]) == 0

    jobs_payload = json.loads((runs_dir / "jobs.json").read_text(encoding="utf-8"))
    assert int(jobs_payload["num_jobs"]) > 0

    assert cli.main(["aggregate", "--results", str(runs_dir), "--out", str(aggregates_dir)]) == 0

    aggregate_manifest = json.loads((aggregates_dir / "aggregate.json").read_text(encoding="utf-8"))
    assert aggregate_manifest["distinct_groups_by_algo"] == {
        "ADR": 12,
        "ADR_MIXRA": 12,
        "UCB": 12,
        "UCB_FORGET": 12,
    }

    assert (
        cli.main(
            [
                "plots",
                "--aggregates-dir",
                str(aggregates_dir / "aggregates"),
                "--out",
                str(figures_dir),
                "--article-profile",
                "full",
            ]
        )
        == 0
    )

    plots_payload = json.loads((figures_dir / "plots_summary.json").read_text(encoding="utf-8"))
    generated_figure_names = {pathlib.Path(path).name for path in plots_payload["figures"]}
    expected = {
        "fig01_pdr_vs_n_snir_off.png",
        "fig02_pdr_vs_n_snir_on.png",
        "fig03_der_vs_n_snir_off.png",
        "fig04_der_vs_n_snir_on.png",
        "fig05_throughput_vs_n_snir_off.png",
        "fig06_throughput_vs_n_snir_on.png",
    }
    assert expected.issubset(generated_figure_names)
    assert plots_payload["article_profile"] == "full"
    fig07_filters = {
        entry["figure"]: entry["filters"] for entry in plots_payload["figure_filters"]
    }["fig07_tc_vs_speed.png"]
    assert fig07_filters["speed"] == ["1", "3", "5"]


def test_cli_e2e_small_grid_run_aggregate_plots_assertions(monkeypatch, tmp_path: pathlib.Path) -> None:
    config_path = pathlib.Path(__file__).resolve().parents[1] / "experiments" / "default.yaml"
    runs_dir = tmp_path / "runs_e2e"
    aggregates_dir = tmp_path / "aggregates_e2e"
    figures_dir = tmp_path / "figures_e2e"

    class _FakeOrchestrator:
        def __init__(self, *, output_root: pathlib.Path):
            self.output_root = pathlib.Path(output_root)

        def execute_jobs(self, jobs, **kwargs):
            reports = []
            for job in jobs:
                params = job["params"]
                run_id = str(params["run_id"])
                algo = str(params["algo"]).upper()
                run_dir = self.output_root / "results" / run_id

                if algo == "ADR":
                    pdr_value, der_value, throughput_value = 0.73, 0.70, 1160.0
                    sf_values = [7, 7, 8, 8, 8]
                else:
                    pdr_value, der_value, throughput_value = 0.91, 0.89, 1450.0
                    sf_values = [9, 9, 10, 10, 10]

                summary_row = {
                    "N": params["N"],
                    "speed": params["speed"],
                    "mobility_model": str(params.get("model", "RWP")).lower(),
                    "mode": str(params["mode"]).lower(),
                    "algo": str(params["algo"]).lower(),
                    "gateways": 1,
                    "sigma": 0.0,
                    "seed": params["seed"],
                    "rep": params["rep"],
                    "run_id": run_id,
                    "duration_s": 12.0,
                    "node_count": params["N"],
                    "tx_count": 100,
                    "success_count": int(round(pdr_value * 100)),
                    "generated_packets": 100,
                    "delivered_bytes": int(throughput_value),
                    "pdr": pdr_value,
                    "der": der_value,
                    "throughput_bps": throughput_value,
                    "Tc_s": 40.0,
                    "jain_fairness": 0.96,
                    "airtime_total_s": 10.5,
                    "airtime_mean_per_node_s": 0.21,
                    "outage_ratio": 0.02,
                    "switch_count": 1,
                }
                _write_csv(run_dir / "summary.csv", list(summary_row.keys()), summary_row)

                event_rows = []
                for idx, sf_value in enumerate(sf_values, start=1):
                    event_rows.append(
                        {
                            "N": params["N"],
                            "speed": params["speed"],
                            "mobility_model": str(params.get("model", "RWP")).lower(),
                            "mode": str(params["mode"]).lower(),
                            "algo": str(params["algo"]).lower(),
                            "gateways": 1,
                            "sigma": 0.0,
                            "seed": params["seed"],
                            "rep": params["rep"],
                            "run_id": run_id,
                            "event_idx": idx,
                            "time_s": float(idx),
                            "event_type": "uplink",
                            "node_id": 0,
                            "sf": sf_value,
                            "sinr_db": 4.0 + idx,
                            "success": 1,
                            "delivered": 1,
                            "payload_bytes": 20,
                            "airtime_s": 0.12,
                            "outage": 0,
                            "switch_count": 0,
                        }
                    )
                _write_csv(run_dir / "events.csv", list(event_rows[0].keys()), event_rows[0])
                with (run_dir / "events.csv").open("a", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(event_rows[0].keys()))
                    for row in event_rows[1:]:
                        writer.writerow(row)

                reports.append(SimpleNamespace(run_id=run_id, success=True, run_dir=run_dir, error=None))

            total = len(jobs)
            return SimpleNamespace(
                reports=reports,
                total_jobs=total,
                skipped_runs=0,
                scheduled_runs=total,
                failed_reports=[],
                interrupted=False,
            )

    monkeypatch.setattr("mobilesfrdth.simulator.engine.GridRunOrchestrator", _FakeOrchestrator)

    grid = "N=30;speed=1;mode=SNIR_ON;algo=ADR,UCB;reps=1;seed_base=55"
    assert cli.main(["run", "--config", str(config_path), "--out", str(runs_dir), "--grid", grid]) == 0
    assert cli.main(["aggregate", "--results", str(runs_dir), "--out", str(aggregates_dir)]) == 0
    assert (
        cli.main(["plots", "--aggregates-dir", str(aggregates_dir / "aggregates"), "--out", str(figures_dir)])
        == 0
    )

    plots_payload = json.loads((figures_dir / "plots_summary.json").read_text(encoding="utf-8"))
    figure_paths = [pathlib.Path(path) for path in plots_payload["figures"]]
    non_empty_figures = [path for path in figure_paths if path.is_file() and path.stat().st_size > 0]
    assert len(non_empty_figures) >= 4

    generated_figure_names = {path.name for path in figure_paths}
    assert "fig09_sf_distribution_snir_on.png" in generated_figure_names
    assert (figures_dir / "fig09_sf_distribution_snir_on.png").stat().st_size > 0

    metric_rows = list(
        csv.DictReader((aggregates_dir / "aggregates" / "metric_by_factor.csv").open("r", encoding="utf-8", newline=""))
    )
    pdr_by_algo = {str(row["algo"]).lower(): float(row["pdr_mean"]) for row in metric_rows}
    assert "adr" in pdr_by_algo and "ucb" in pdr_by_algo
    assert pdr_by_algo["adr"] != pdr_by_algo["ucb"]

    distribution_rows = list(
        csv.DictReader((aggregates_dir / "aggregates" / "distribution_sf.csv").open("r", encoding="utf-8", newline=""))
    )
    assert distribution_rows
    assert any(float(row.get("count", 0) or 0) > 0 for row in distribution_rows)

def test_cli_diagnose_builds_top_errors_and_report(tmp_path: pathlib.Path) -> None:
    runs_dir = tmp_path / "campaign"
    results_dir = runs_dir / "results"
    run_a_dir = results_dir / "run_a"
    run_b_dir = results_dir / "run_b"
    run_a_dir.mkdir(parents=True, exist_ok=True)
    run_b_dir.mkdir(parents=True, exist_ok=True)

    batch_summary = {
        "num_failures": 2,
        "failures": [
            {
                "run_id": "run_a",
                "error": json.dumps({"error_type": "ValueError", "message": "invalid time_bin_s value"}),
                "run_dir": str(run_a_dir),
            },
            {
                "run_id": "run_b",
                "error": json.dumps({"error_type": "TimeoutError", "message": "max-walltime reached"}),
                "run_dir": str(run_b_dir),
            },
        ],
    }
    (runs_dir / "batch_summary.json").write_text(json.dumps(batch_summary), encoding="utf-8")

    campaign_entries = [
        {"step": "run", "out_dir": str(runs_dir)},
        {"step": "aggregate", "message": "aggregate completed"},
    ]
    (runs_dir / "campaign_log.jsonl").write_text(
        "\n".join(json.dumps(entry) for entry in campaign_entries) + "\n",
        encoding="utf-8",
    )

    (run_a_dir / "run.log").write_text(
        "2026-01-01 00:00:00,000 | ERROR | invalid time_bin_s value\n",
        encoding="utf-8",
    )
    (run_b_dir / "run.log").write_text(
        "2026-01-01 00:00:01,000 | ERROR | max-walltime reached\n",
        encoding="utf-8",
    )

    assert cli.main(["diagnose", "--results", str(runs_dir), "--top", "5"]) == 0

    report = json.loads((runs_dir / "diagnostics_report.json").read_text(encoding="utf-8"))
    assert report["total_error_entries"] >= 4
    assert report["top_errors"]
    assert any(item["type"] == "ValueError" for item in report["top_errors"])
    assert any(item["type"] == "RuntimeError" for item in report["top_errors"])
    suggested_parameters = {item["parameter"] for item in report["parameter_suggestions"]}
    assert "time_bin_s" in suggested_parameters
    assert "duration_s" in suggested_parameters

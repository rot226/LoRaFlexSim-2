from __future__ import annotations

import csv
import json
import pathlib
import sys
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

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
    "fig09_sf_distribution.png",
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
    assert len(result_run_dirs) == num_jobs

    assert cli.main(["aggregate", "--results", str(runs_dir), "--out", str(aggregates_dir)]) == 0

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
    assert _NON_BONUS_FIGURES.issubset(generated_figure_names)

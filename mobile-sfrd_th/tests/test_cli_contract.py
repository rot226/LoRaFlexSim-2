import json
from pathlib import Path

import mobilesfrdth.cli as cli
from mobilesfrdth.cli import main
import subprocess
import sys
from mobilesfrdth.plotting.plots import validate_aggregates_inputs


def test_plots_returns_non_zero_if_required_csv_missing(tmp_path: Path):
    aggregates = tmp_path / "aggregates"
    aggregates.mkdir(parents=True)

    code = main(["plots", "--aggregates-dir", str(aggregates), "--out", str(tmp_path / "plots")])

    assert code != 0


def test_validate_aggregates_inputs_reports_missing_columns(tmp_path: Path):
    aggregates = tmp_path / "aggregates"
    aggregates.mkdir(parents=True)

    (aggregates / "metric_by_factor.csv").write_text("N,algo\n50,ucb\n", encoding="utf-8")
    (aggregates / "distribution_sf.csv").write_text("algo,sf,ratio\nucb,7,0.5\n", encoding="utf-8")
    (aggregates / "convergence_tc.csv").write_text("algo,speed,Tc_s\nucb,1.0,10\n", encoding="utf-8")
    (aggregates / "sinr_cdf.csv").write_text("algo,quantile,sinr_db\nucb,0.5,2.0\n", encoding="utf-8")
    (aggregates / "fairness_airtime_switching.csv").write_text(
        "N,algo,jain_fairness,airtime_total_s,switch_count\n50,ucb,0.9,12,1\n",
        encoding="utf-8",
    )

    errors = validate_aggregates_inputs(aggregates)

    assert any("metric_by_factor.csv" in err for err in errors)
    assert any("mode" in err for err in errors)


def test_aggregate_returns_non_zero_when_no_run_found(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()

    code = main(["aggregate", "--results", str(empty), "--out", str(tmp_path / "out")])

    assert code != 0


def test_verbose_and_quiet_are_mutually_exclusive(tmp_path: Path):
    aggregates = tmp_path / "aggregates"
    aggregates.mkdir()

    code = main(["--verbose", "--quiet", "plots", "--aggregates-dir", str(aggregates), "--out", str(tmp_path / "plots")])

    assert code != 0


def test_keyboard_interrupt_in_aggregate_writes_partial_and_returns_130(tmp_path: Path, monkeypatch):
    def _boom(*, inputs, output_root, progress_callback=None):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "aggregate_runs", _boom)

    out = tmp_path / "agg_out"
    code = main(["aggregate", "--results", str(tmp_path), "--out", str(out)])

    assert code == 130
    partial = out / "aggregate_partial.json"
    assert partial.is_file()
    payload = json.loads(partial.read_text(encoding="utf-8"))
    assert payload["status"] == "interrupted"
    assert payload["message"] == "reprendre via --resume"


def test_cli_aggregate_supports_paths_with_spaces_and_parentheses(tmp_path: Path):
    run_root = tmp_path / "résultats (test espace)"
    run_dir = run_root / "results" / "run_01"
    run_dir.mkdir(parents=True)

    (run_dir / "summary.csv").write_text(
        "N,speed,mobility_model,mode,algo,gateways,sigma,seed,rep,run_id,duration_s,node_count,tx_count,success_count,generated_packets,delivered_bytes,pdr,der,throughput_bps,Tc_s,jain_fairness,airtime_total_s,airtime_mean_per_node_s,outage_ratio,switch_count\n"
        "50,1.0,rwp,adr,ucb,2,4.0,1,0,run_01,10,2,2,1,2,12,0.5,0.5,9.6,1.0,1.0,0.12,0.06,0.5,1\n",
        encoding="utf-8",
    )
    (run_dir / "events.csv").write_text(
        "N,speed,mobility_model,mode,algo,gateways,sigma,seed,rep,run_id,event_idx,time_s,event_type,node_id,sf,sinr_db,success,delivered,payload_bytes,airtime_s,outage,switch_count\n"
        "50,1.0,rwp,adr,ucb,2,4.0,1,0,run_01,0,1.0,uplink,1,7,5.0,1,1,12,0.05,0,1\n"
        "50,1.0,rwp,adr,ucb,2,4.0,1,0,run_01,1,2.0,uplink,2,8,-2.0,0,0,12,0.07,1,0\n",
        encoding="utf-8",
    )
    (run_dir / "node_timeseries.csv").write_text(
        "N,speed,mobility_model,mode,algo,gateways,sigma,seed,rep,run_id,bin_start_s,bin_end_s,node_id,tx_count,success_count,delivery_ratio,throughput_bps,mean_sinr_db,airtime_s,outage_count,switch_count\n"
        "50,1.0,rwp,adr,ucb,2,4.0,1,0,run_01,0,10,1,1,1,1.0,9.6,5.0,0.05,0,1\n"
        "50,1.0,rwp,adr,ucb,2,4.0,1,0,run_01,0,10,2,1,0,0.0,0.0,-2.0,0.07,1,0\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "sortie (agrégée)"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mobilesfrdth.cli",
            "aggregate",
            "--results",
            str(run_root),
            "--out",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (out_dir / "aggregate.json").is_file()
    assert (out_dir / "aggregates" / "metric_by_factor.csv").is_file()
    plots_out = tmp_path / "figures (test)"
    plots_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mobilesfrdth.cli",
            "plots",
            "--aggregates-dir",
            str(out_dir / "aggregates"),
            "--out",
            str(plots_out),
            "--no-bonus",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert plots_result.returncode == 0, plots_result.stderr
    assert (plots_out / "plots_summary.json").is_file()

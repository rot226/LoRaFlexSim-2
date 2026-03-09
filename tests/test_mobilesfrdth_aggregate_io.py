import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from mobilesfrdth.simulator.io import SUMMARY_COLUMNS, aggregate_runs, write_run_outputs


def _write_csv(path: pathlib.Path, headers: list[str], row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerow({header: row.get(header, "") for header in headers})


def _summary_row(run_id: str) -> dict[str, object]:
    return {
        "N": "50",
        "speed": "1",
        "mobility_model": "rwp",
        "mode": "snir_on",
        "algo": "ucb",
        "gateways": "1",
        "sigma": "2",
        "seed": "1",
        "rep": "0",
        "run_id": run_id,
        "duration_s": "100",
        "node_count": "50",
        "tx_count": "10",
        "success_count": "9",
        "generated_packets": "10",
        "delivered_bytes": "450",
        "pdr": "0.9",
        "der": "0.9",
        "throughput_bps": "36",
        "Tc_s": "25",
        "jain_fairness": "0.95",
        "airtime_total_s": "12.5",
        "airtime_mean_per_node_s": "0.25",
        "outage_ratio": "0.1",
        "switch_count": "3",
    }


def test_aggregate_runs_summary_only_reads_only_summary(tmp_path, capsys):
    run_dir = tmp_path / "results" / "run_001"
    _write_csv(run_dir / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_001"))

    files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=True)

    captured = capsys.readouterr()
    assert "Dossiers traités: 1/1" in captured.out
    assert set(files) == {"metric_by_factor", "convergence_tc", "fairness_airtime_switching"}
    for path in files.values():
        assert path.is_file()


def test_aggregate_runs_skip_flags_control_event_outputs(tmp_path):
    run_dir = tmp_path / "results" / "run_001"
    _write_csv(run_dir / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_001"))
    _write_csv(
        run_dir / "events.csv",
        ["event_type", "N", "speed", "mobility_model", "mode", "algo", "gateways", "sigma", "sf", "sinr_db"],
        {
            "event_type": "uplink",
            "N": "50",
            "speed": "1",
            "mobility_model": "rwp",
            "mode": "snir_on",
            "algo": "ucb",
            "gateways": "1",
            "sigma": "2",
            "sf": "9",
            "sinr_db": "6.5",
        },
    )

    files = aggregate_runs(
        inputs=[tmp_path],
        output_root=tmp_path / "out",
        skip_sinr_cdf=True,
        skip_sf_distribution=False,
    )

    assert "distribution_sf" in files
    assert "sinr_cdf" not in files
    assert files["distribution_sf"].is_file()


def test_aggregate_runs_sinr_cdf_has_strict_columns(tmp_path):
    run_dir = tmp_path / "results" / "run_001"
    _write_csv(run_dir / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_001"))
    _write_csv(
        run_dir / "events.csv",
        ["event_type", "N", "speed", "mobility_model", "mode", "algo", "gateways", "sigma", "sf", "sinr_db"],
        {
            "event_type": "uplink",
            "N": "50",
            "speed": "3",
            "mobility_model": "rwp",
            "mode": "snir_on",
            "algo": "ucb",
            "gateways": "1",
            "sigma": "2",
            "sf": "9",
            "sinr_db": "6.5",
        },
    )

    files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=False)

    with files["sinr_cdf"].open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["algo", "mode", "N", "speed", "quantile", "sinr_db"]



def test_tc_is_computed_from_node_timeseries_and_varies_with_scenario(tmp_path):
    def _events(success_pattern: list[int], *, per_bin: int = 10) -> list[dict[str, object]]:
        events: list[dict[str, object]] = []
        for bin_index, successes in enumerate(success_pattern):
            time_s = float(bin_index * 10 + 1)
            for packet in range(per_bin):
                ok = packet < successes
                events.append(
                    {
                        "event_type": "uplink",
                        "time_s": time_s,
                        "node_id": packet % 5,
                        "success": ok,
                        "delivered": ok,
                        "payload_bytes": 20,
                        "snr_db": 5.0,
                        "sinr_db": 4.0,
                        "airtime_s": 0.05,
                        "outage": int(not ok),
                        "switch_count": 0,
                    }
                )
        return events

    write_run_outputs(
        output_root=tmp_path,
        run_id="tc_small",
        run_config={"N": 40, "speed": 0.5, "mobility_model": "rwp", "mode": "snir_on", "algo": "adr", "gateways": 1, "sigma": 1, "seed": 1, "rep": 0},
        events=_events([1, 3, 5, 7, 8, 9]),
        duration_s=60.0,
        time_bin_s=10.0,
    )
    write_run_outputs(
        output_root=tmp_path,
        run_id="tc_large",
        run_config={"N": 140, "speed": 3.0, "mobility_model": "rwp", "mode": "snir_on", "algo": "adr", "gateways": 1, "sigma": 1, "seed": 2, "rep": 0},
        events=_events([0, 0, 1, 2, 3, 9]),
        duration_s=60.0,
        time_bin_s=10.0,
    )

    def _tc(run_id: str) -> float:
        with (tmp_path / "results" / run_id / "summary.csv").open("r", encoding="utf-8", newline="") as handle:
            return float(next(csv.DictReader(handle))["Tc_s"])

    tc_small = _tc("tc_small")
    tc_large = _tc("tc_large")

    assert tc_small != tc_large
    assert tc_small > 0.0
    assert tc_large > 0.0

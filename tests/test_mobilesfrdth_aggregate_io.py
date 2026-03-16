import csv
import json
import pathlib
import sys
import warnings

import pytest

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
    assert set(files) == {
        "metric_by_factor",
        "convergence_tc",
        "fairness_airtime_switching",
        "pareto_reliability_airtime",
        "outage_probability",
        "energy_efficiency_reliability",
    }
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
        assert reader.fieldnames == ["N", "speed", "mobility_model", "mode", "algo", "gateways", "sigma_shadowing", "quantile", "sinr_db", "sample_count"]
        rows = list(reader)
        assert rows
        assert rows[0]["quantile"] == "1.0"
        assert rows[0]["sample_count"] == "1"


def test_aggregate_runs_computes_ci95_and_effective_runs(tmp_path):
    run_base = tmp_path / "results"
    run_1 = run_base / "run_001"
    run_2 = run_base / "run_002"
    _write_csv(run_1 / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_001"))
    row2 = _summary_row("run_002")
    row2["pdr"] = "0.7"
    _write_csv(run_2 / "summary.csv", SUMMARY_COLUMNS, row2)

    files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=True)

    rows = list(csv.DictReader(files["metric_by_factor"].open("r", encoding="utf-8", newline="")))
    assert len(rows) == 1
    row = rows[0]
    assert row["n_runs_effective"] == "2"
    assert row["num_runs"] == "2"
    assert float(row["pdr_mean"]) == 0.8
    assert float(row["pdr_ci95"]) > 0.0
    assert float(row["pdr_std"]) > 0.0
    assert row["pdr_n"] == "2"
    assert float(row["pdr_ci95_low"]) < float(row["pdr_mean"]) < float(row["pdr_ci95_high"])


def test_aggregate_runs_reports_ignored_corrupted_runs(tmp_path):
    valid_run = tmp_path / "results" / "run_ok"
    bad_run = tmp_path / "results" / "run_bad"
    _write_csv(valid_run / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_ok"))
    broken = _summary_row("run_bad")
    broken["pdr"] = "not-a-number"
    _write_csv(bad_run / "summary.csv", SUMMARY_COLUMNS, broken)

    ignored_runs: list[dict[str, str]] = []
    files = aggregate_runs(
        inputs=[tmp_path],
        output_root=tmp_path / "out",
        summary_only=True,
        ignored_runs_report=ignored_runs,
    )

    assert files["metric_by_factor"].is_file()
    assert len(ignored_runs) == 1
    assert ignored_runs[0]["reason"] == "csv_corrupted"



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

    assert tc_small > 0.0
    assert tc_large > 0.0
    # Sensibilité SNIR_ON: charge/vitesse plus élevées -> convergence plus lente.
    assert tc_large >= tc_small


def test_aggregate_runs_writes_bonus_aggregate_files(tmp_path):
    run_dir = tmp_path / "results" / "run_001"
    _write_csv(run_dir / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_001"))

    files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=True)

    with files["pareto_reliability_airtime"].open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {"pdr_mean", "pdr_ci95", "airtime_total_s_mean", "airtime_total_s_ci95"}.issubset(rows[0])

    with files["outage_probability"].open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert rows[0]["mode"] == "snir_on"
    assert {"outage_prob_mean", "outage_prob_ci95"}.issubset(rows[0])

    with files["energy_efficiency_reliability"].open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {"pdr_mean", "pdr_ci95", "energy_efficiency_mean", "energy_efficiency_ci95"}.issubset(rows[0])


def test_write_run_outputs_skips_uplink_without_explicit_success_and_delivered(tmp_path):
    events = [
        {
            "event_type": "uplink",
            "time_s": 1.0,
            "node_id": 1,
            "payload_bytes": 20,
        },
        {
            "event_type": "uplink",
            "time_s": 2.0,
            "node_id": 1,
            "success": True,
            "delivered": True,
            "payload_bytes": 20,
        },
    ]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        write_run_outputs(
            output_root=tmp_path,
            run_id="missing_uplink_fields",
            run_config={"N": 1, "speed": 0.0, "mobility_model": "rwp", "mode": "snir_on", "algo": "adr", "gateways": 1, "sigma": 1, "seed": 1, "rep": 0},
            events=events,
            duration_s=10.0,
        )

    messages = [str(w.message) for w in caught]
    assert any("Événement uplink invalide ignoré" in msg for msg in messages)
    assert any("1 événement(s) invalide(s) ignoré(s)" in msg for msg in messages)

    summary_path = tmp_path / "results" / "missing_uplink_fields" / "summary.csv"
    summary_row = next(csv.DictReader(summary_path.open("r", encoding="utf-8", newline="")))
    assert int(summary_row["tx_count"]) == 1
    assert int(summary_row["success_count"]) == 1


def test_write_run_outputs_validates_required_fields(tmp_path):
    events = [
        {
            "time_s": 1.0,
            "node_id": 1,
            "success": True,
            "delivered": True,
        },
        {
            "event_type": "uplink",
            "time_s": 2.0,
            "node_id": 1,
            "success": True,
            "delivered": True,
            "payload_bytes": 20,
        },
    ]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        write_run_outputs(
            output_root=tmp_path,
            run_id="missing_required_fields",
            run_config={"N": 1, "speed": 0.0, "mobility_model": "rwp", "mode": "snir_on", "algo": "adr", "gateways": 1, "sigma": 1, "seed": 1, "rep": 0},
            events=events,
            duration_s=10.0,
        )

    messages = [str(w.message) for w in caught]
    assert any("champ(s) obligatoire(s) manquant(s): event_type" in msg for msg in messages)

    events_path = tmp_path / "results" / "missing_required_fields" / "events.csv"
    rows = list(csv.DictReader(events_path.open("r", encoding="utf-8", newline="")))
    assert len(rows) == 1


def test_write_run_outputs_uses_switch_deltas_and_explicit_success_fairness(tmp_path):
    events = [
        {
            "event_type": "uplink",
            "time_s": 1.0,
            "node_id": 1,
            "success": True,
            "delivered": True,
            "payload_bytes": 20,
            "switch_count": 0,
        },
        {
            "event_type": "uplink",
            "time_s": 2.0,
            "node_id": 1,
            "success": True,
            "delivered": True,
            "payload_bytes": 20,
            "switch_count": 1,
        },
        {
            "event_type": "uplink",
            "time_s": 3.0,
            "node_id": 1,
            "success": False,
            "delivered": False,
            "payload_bytes": 20,
            "switch_count": 1,
        },
        {
            "event_type": "uplink",
            "time_s": 4.0,
            "node_id": 2,
            "success": False,
            "delivered": False,
            "payload_bytes": 20,
            "switch_count": 0,
        },
        {
            "event_type": "uplink",
            "time_s": 5.0,
            "node_id": 1,
            "success": False,
            "delivered": False,
            "payload_bytes": 20,
            "switch_count": 2,
        },
    ]

    write_run_outputs(
        output_root=tmp_path,
        run_id="switch_delta_and_fairness",
        run_config={"N": 2, "speed": 0.0, "mobility_model": "rwp", "mode": "snir_on", "algo": "adr", "gateways": 1, "sigma": 1, "seed": 1, "rep": 0},
        events=events,
        duration_s=10.0,
    )

    summary_path = tmp_path / "results" / "switch_delta_and_fairness" / "summary.csv"
    summary_row = next(csv.DictReader(summary_path.open("r", encoding="utf-8", newline="")))
    assert int(summary_row["switch_count"]) == 2
    assert float(summary_row["jain_fairness"]) == 0.5

    node_timeseries_path = tmp_path / "results" / "switch_delta_and_fairness" / "node_timeseries.csv"
    node_rows = list(csv.DictReader(node_timeseries_path.open("r", encoding="utf-8", newline="")))
    switch_total = sum(int(row["switch_count"]) for row in node_rows)
    assert switch_total == 2


def test_aggregate_runs_writes_diagnostics_and_warns_on_partial_valid_runs(tmp_path):
    valid_run = tmp_path / "results" / "run_ok"
    missing_events = tmp_path / "results" / "run_missing_events"
    corrupted_events = tmp_path / "results" / "run_bad_events"

    _write_csv(valid_run / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_ok"))
    _write_csv(
        valid_run / "events.csv",
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

    _write_csv(missing_events / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_missing_events"))

    _write_csv(corrupted_events / "summary.csv", SUMMARY_COLUMNS, _summary_row("run_bad_events"))
    _write_csv(
        corrupted_events / "events.csv",
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
            "sinr_db": "not-a-number",
        },
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=False)

    assert files["metric_by_factor"].is_file()
    diagnostics_path = (tmp_path / "out" / "aggregates" / "aggregate_diagnostics.json")
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))

    assert diagnostics["counts"]["discovered_runs"] == 3
    assert diagnostics["counts"]["valid_runs"] == 1
    assert diagnostics["counts"]["incomplete_runs"] == 2
    assert any(entry["reason"] == "events_absent" for entry in diagnostics["incomplete_runs"])
    assert any(entry["reason"] == "csv_corrupted" for entry in diagnostics["incomplete_runs"])
    assert any(entry["run_id"] == "run_ok" for entry in diagnostics["complete_runs"])
    assert any("incomplet(s)/corrompu(s)" in str(w.message) for w in caught)


def test_aggregate_runs_fails_with_guided_message_when_no_valid_runs(tmp_path):
    run_dir = tmp_path / "results" / "run_missing_summary"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        run_dir / "events.csv",
        ["event_type", "sinr_db"],
        {"event_type": "uplink", "sinr_db": "1.0"},
    )

    with pytest.raises(ValueError, match="aucun run valide") as excinfo:
        aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=False)

    message = str(excinfo.value).lower()
    assert "runs détectés" in message
    assert "--verbose" in message

    diagnostics_path = tmp_path / "out" / "aggregates" / "aggregate_diagnostics.json"
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    assert diagnostics["counts"]["discovered_runs"] == 1
    assert diagnostics["counts"]["valid_runs"] == 0
    assert diagnostics["incomplete_runs"][0]["reason"] == "summary_absent"


def test_aggregate_runs_fails_with_guided_message_when_no_run_dir_found(tmp_path):
    with pytest.raises(ValueError, match="Aucun dossier de run détecté") as excinfo:
        aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=True)

    assert "--verbose" in str(excinfo.value)


def test_aggregate_runs_legacy_sigma_columns_are_read_and_rewritten_as_sigma_shadowing(tmp_path):
    run_dir = tmp_path / "results" / "run_legacy"
    _write_csv(
        run_dir / "summary.csv",
        [column if column != "sigma_shadowing" else "sigma" for column in SUMMARY_COLUMNS],
        _summary_row("run_legacy"),
    )
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

    files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=False)

    metric_rows = list(csv.DictReader(files["metric_by_factor"].open("r", encoding="utf-8", newline="")))
    assert metric_rows
    assert "sigma_shadowing" in metric_rows[0]
    assert "sigma" not in metric_rows[0]
    assert metric_rows[0]["sigma_shadowing"] == "2"

    sinr_rows = list(csv.DictReader(files["sinr_cdf"].open("r", encoding="utf-8", newline="")))
    assert sinr_rows
    assert "sigma_shadowing" in sinr_rows[0]
    assert "sigma" not in sinr_rows[0]
    assert sinr_rows[0]["sigma_shadowing"] == "2"

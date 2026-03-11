from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from mobilesfrdth.simulator.engine import EventDrivenEngine, Node
from mobilesfrdth.simulator.io import write_run_outputs


def _run_summary(
    tmp_path: pathlib.Path, *, run_id: str, n: int, mode: str, speed: float = 1.0
) -> dict[str, float]:
    engine = EventDrivenEngine(seed=123)
    nodes = [Node(node_id=i + 1, period_s=30.0, payload_size=20) for i in range(n)]
    result = engine.run(
        nodes=nodes,
        until_s=600.0,
        mode=mode,
        algo="adr",
        interference_db=6.0,
        sigma=1.0,
    )
    write_run_outputs(
        output_root=tmp_path,
        run_id=run_id,
        run_config={
            "N": n,
            "speed": speed,
            "mobility_model": "rwp",
            "mode": mode,
            "algo": "adr",
            "gateways": 1,
            "sigma": 1.0,
            "seed": 123,
            "rep": 1,
        },
        events=result.events,
        duration_s=600.0,
        time_bin_s=60.0,
    )
    summary_path = tmp_path / "results" / run_id / "summary.csv"
    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    return {
        "pdr": float(row["pdr"]),
        "throughput_bps": float(row["throughput_bps"]),
        "switch_count": float(row["switch_count"]),
        "Tc_s": float(row["Tc_s"]),
    }


def test_non_regression_metrics_vary_with_network_size_and_mode(tmp_path: pathlib.Path) -> None:
    small_off = _run_summary(tmp_path, run_id="small_off", n=20, mode="snir_off")
    large_off = _run_summary(tmp_path, run_id="large_off", n=120, mode="snir_off")
    large_on = _run_summary(tmp_path, run_id="large_on", n=120, mode="snir_on")

    assert (
        small_off["pdr"] != large_off["pdr"]
        or small_off["throughput_bps"] != large_off["throughput_bps"]
        or small_off["switch_count"] != large_off["switch_count"]
    )
    assert (
        large_off["pdr"] != large_on["pdr"]
        or large_off["throughput_bps"] != large_on["throughput_bps"]
        or large_off["switch_count"] != large_on["switch_count"]
    )



def test_switch_count_stays_zero_when_sf_constant(monkeypatch) -> None:
    monkeypatch.setattr(
        "mobilesfrdth.simulator.engine.recommend_sf_with_reason",
        lambda *, current_sf, snr_db, cfg: (current_sf, "test_margin"),
    )
    engine = EventDrivenEngine(seed=42)
    nodes = [Node(node_id=1, period_s=30.0, payload_size=12)]

    result = engine.run(
        nodes=nodes,
        until_s=300.0,
        mode="snir_off",
        algo="adr",
        interference_db=0.0,
        sigma=0.0,
    )

    assert result.events
    assert all(event.switch_count == 0 for event in result.events)
    assert nodes[0].meta["switch_count"] == 0


def test_switch_count_increases_when_sf_is_adaptive(monkeypatch) -> None:
    monkeypatch.setattr(
        "mobilesfrdth.simulator.engine.recommend_sf_with_reason",
        lambda *, current_sf, snr_db, cfg: ((8 if current_sf == 7 else 7), "test_margin"),
    )
    engine = EventDrivenEngine(seed=42)
    nodes = [Node(node_id=1, period_s=30.0, payload_size=12, meta={"sf": 7})]

    result = engine.run(
        nodes=nodes,
        until_s=300.0,
        mode="snir_off",
        algo="adr",
        interference_db=0.0,
        sigma=0.0,
    )

    assert result.events
    assert any(event.switch_count == 1 for event in result.events)
    assert nodes[0].meta["switch_count"] > 0


def test_all_algorithms_update_sf_via_common_interface(monkeypatch) -> None:
    def _run(algo: str) -> int:
        engine = EventDrivenEngine(seed=7)
        calls: list[str] = []

        def fake_select(**kwargs):
            calls.append(kwargs["algo_name"])
            return kwargs["current_sf"], "test_common"

        monkeypatch.setattr(engine, "_select_next_sf", fake_select)
        nodes = [Node(node_id=1, period_s=30.0, payload_size=12)]
        result = engine.run(
            nodes=nodes,
            until_s=90.0,
            mode="snir_off",
            algo=algo,
            interference_db=0.0,
            sigma=0.0,
        )
        assert result.events
        assert calls and all(name == algo for name in calls)
        return nodes[0].meta["sf"]

    sf_adr = _run("adr")
    sf_adr_mixra = _run("adr_mixra")
    sf_ucb = _run("ucb")
    sf_ucb_forget = _run("ucb_forget")

    assert isinstance(sf_adr, int)
    assert isinstance(sf_adr_mixra, int)
    assert isinstance(sf_ucb, int)
    assert isinstance(sf_ucb_forget, int)


def test_success_decision_delegated_to_interference_module(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_transmission_success(*args, **kwargs):
        calls["count"] += 1
        return (calls["count"] % 2 == 0), -3.0

    monkeypatch.setattr("mobilesfrdth.simulator.engine.transmission_success", fake_transmission_success)

    engine = EventDrivenEngine(seed=42)
    nodes = [Node(node_id=1, period_s=30.0, payload_size=12)]
    result = engine.run(
        nodes=nodes,
        until_s=120.0,
        mode="snir_on",
        algo="adr",
        interference_db=4.0,
        sigma=1.0,
    )

    assert calls["count"] == len(result.events)
    assert [event.success for event in result.events] == [False, True, False, True]
    assert all(event.threshold_db != 0.0 for event in result.events)


def test_events_csv_includes_radio_decision_fields(tmp_path: pathlib.Path) -> None:
    engine = EventDrivenEngine(seed=10)
    nodes = [Node(node_id=1, period_s=30.0, payload_size=12)]
    result = engine.run(
        nodes=nodes,
        until_s=60.0,
        mode="snir_on",
        algo="adr",
        interference_db=4.0,
        sigma=0.5,
    )

    write_run_outputs(
        output_root=tmp_path,
        run_id="radio_fields",
        run_config={
            "N": 1,
            "speed": 1.0,
            "mobility_model": "rwp",
            "mode": "snir_on",
            "algo": "adr",
            "gateways": 1,
            "sigma": 0.5,
            "seed": 10,
            "rep": 1,
        },
        events=result.events,
        duration_s=60.0,
        time_bin_s=30.0,
    )

    events_path = tmp_path / "results" / "radio_fields" / "events.csv"
    with events_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        assert "sinr_db" in reader.fieldnames
        assert "snr_db" in reader.fieldnames
        assert "threshold_db" in reader.fieldnames
        assert "success" in reader.fieldnames
        assert "decision_reason" in reader.fieldnames
        assert "target_sf" in reader.fieldnames

        rows = list(reader)
        assert rows
        assert all(row["decision_reason"] != "" for row in rows)


def test_run_log_contains_sinr_success_diagnostic(tmp_path: pathlib.Path) -> None:
    from mobilesfrdth.simulator.engine import GridRunOrchestrator

    orchestrator = GridRunOrchestrator(output_root=tmp_path)
    report = orchestrator.execute_jobs(
        [
            {
                "job_id": "diag",
                "params": {
                    "run_id": "diag",
                    "N": 5,
                    "period_s": 30.0,
                    "duration_s": 120.0,
                    "mode": "snir_on",
                    "algo": "adr",
                    "sigma": 1.0,
                    "seed": 5,
                },
            }
        ]
    )

    assert report.reports and report.reports[0].success
    run_log = (tmp_path / "results" / "diag" / "run.log").read_text(encoding="utf-8")
    assert "Diagnostic SINR->success run_id=diag" in run_log
    assert "Diagnostic SINR bin" in run_log


def test_sf_distributions_differ_between_adr_and_adr_mixra() -> None:
    def _distribution(algo: str) -> dict[int, int]:
        engine = EventDrivenEngine(seed=77)
        nodes = [Node(node_id=i + 1, period_s=20.0, payload_size=24) for i in range(35)]
        result = engine.run(
            nodes=nodes,
            until_s=900.0,
            mode="snir_on",
            algo=algo,
            interference_db=6.0,
            sigma=1.2,
        )
        dist: dict[int, int] = {}
        for event in result.events:
            dist[event.sf] = dist.get(event.sf, 0) + 1
        return dist

    adr_dist = _distribution("adr")
    mixra_dist = _distribution("adr_mixra")

    assert adr_dist != mixra_dist

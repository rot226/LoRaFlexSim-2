from __future__ import annotations

from pathlib import Path
from typing import Any

from mobilesfrdth.jamming import cli
from mobilesfrdth.jamming.campaigns import JammingRunKey
from mobilesfrdth.jamming.runner import JammingRunResult, run_jamming_simulation


def test_run_jamming_simulation_progress_finishes_at_one() -> None:
    progress_values: list[float] = []

    run_jamming_simulation(
        node_count=1,
        until_s=0.2,
        seed=1,
        period_s=0.1,
        progress_callback=lambda progress, _context: progress_values.append(progress),
    )

    assert progress_values
    assert progress_values[-1] == 1.0


def test_run_jamming_simulation_progress_values_are_monotonic() -> None:
    progress_values: list[float] = []

    run_jamming_simulation(
        node_count=2,
        until_s=0.3,
        seed=2,
        period_s=0.1,
        progress_callback=lambda progress, _context: progress_values.append(progress),
    )

    assert progress_values == sorted(progress_values)
    assert progress_values[-1] == 1.0


def _minimal_result() -> JammingRunResult:
    return JammingRunResult(
        raw_events=[],
        metrics_by_node={},
        channel_sf_timeseries=[],
        run_summary={
            "scenario": "stub",
            "nodes": 1,
            "adr": "on",
            "seed": 0,
            "until_s": 0.1,
            "legitimate_packet_count": 0,
            "received_packets": 0,
            "lost_packets": 0,
            "jammed_packets": 0,
            "pdr": 0.0,
            "node_count": 1,
            "jamming_window_count": 0,
            "jamming_windows": [],
        },
        legitimate_nodes=[],
    )


def _run_args(tmp_path: Path) -> list[str]:
    return [
        "run",
        "--scenario",
        "stub",
        "--nodes",
        "1",
        "--adr",
        "on",
        "--seed",
        "0",
        "--sim-time",
        "0.1",
        "--channels",
        "868.1",
        "--jammed-channel",
        "868.1",
        "--channel-selection",
        "static",
        "--out",
        str(tmp_path),
        "--time-bin-size",
        "0.1",
        "--progress-step",
        "1",
    ]


def test_cmd_run_prints_progress_percent(tmp_path: Path, monkeypatch, capsys) -> None:
    def fake_run_jamming_simulation(**kwargs: Any) -> JammingRunResult:
        callback = kwargs["progress_callback"]
        assert kwargs["until_s"] == 0.1
        callback(1.0, {"time_s": 0.1, "tx_packets": 0, "rx_packets": 0, "jammed_packets": 0})
        return _minimal_result()

    monkeypatch.setattr(cli, "run_jamming_simulation", fake_run_jamming_simulation)
    monkeypatch.setattr(cli, "write_run_csvs", lambda *_args, **_kwargs: None)

    exit_code = cli.main(_run_args(tmp_path))

    assert exit_code == 0
    assert "%" in capsys.readouterr().out


def _campaign_args(tmp_path: Path) -> list[str]:
    return [
        "campaign",
        "--scenario",
        "stub",
        "--nodes",
        "1",
        "--adr",
        "on",
        "--seeds",
        "0",
        "--sim-time",
        "0.1",
        "--channels",
        "868.1",
        "--jammed-channel",
        "868.1",
        "--channel-selection",
        "static",
        "--out",
        str(tmp_path),
        "--time-bin-size",
        "0.1",
        "--progress-step",
        "1",
    ]


def test_cmd_campaign_prints_global_progress_percent(tmp_path: Path, monkeypatch, capsys) -> None:
    def fake_run_campaign(**kwargs: Any) -> tuple[JammingRunKey, ...]:
        callback = kwargs["progress_callback"]
        run_key = JammingRunKey("stub", 1, True, 0, "static")
        callback(run_key, 1, 1, 1.0, {"run_progress": 1.0})
        return (run_key,)

    monkeypatch.setattr(cli, "run_campaign", fake_run_campaign)

    exit_code = cli.main(_campaign_args(tmp_path))
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "run 1/" in output
    assert "% global" in output
    assert "100.0 %" in output

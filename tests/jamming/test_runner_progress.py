from __future__ import annotations

from mobilesfrdth.jamming.runner import run_jamming_simulation


def test_run_jamming_simulation_reports_progress_context_and_final_completion() -> None:
    calls: list[tuple[float, dict]] = []

    result = run_jamming_simulation(
        node_count=2,
        until_s=120.0,
        seed=123,
        period_s=30.0,
        progress_callback=lambda progress, context: calls.append((progress, context.copy())),
    )

    assert calls
    final_progress, final_context = calls[-1]
    assert final_progress == 1.0
    assert final_context["time_s"] == 120.0
    assert final_context["until_s"] == 120.0
    assert final_context["node_count"] == 2
    assert final_context["seed"] == 123
    assert final_context["tx_packets"] == result.run_summary["legitimate_packet_count"]
    assert final_context["rx_packets"] == result.run_summary["received_packets"]
    assert final_context["jammed_packets"] == result.run_summary["jammed_packets"]
    assert {"time_s", "until_s", "node_count", "seed", "tx_packets", "rx_packets", "jammed_packets"} <= final_context.keys()


def test_run_jamming_simulation_reports_final_progress_for_empty_fast_run() -> None:
    calls: list[tuple[float, dict]] = []

    run_jamming_simulation(
        node_count=0,
        until_s=0.0,
        seed=7,
        progress_callback=lambda progress, context: calls.append((progress, context.copy())),
    )

    assert calls == [
        (
            1.0,
            {
                "time_s": 0.0,
                "until_s": 0.0,
                "node_count": 0,
                "seed": 7,
                "tx_packets": 0,
                "rx_packets": 0,
                "jammed_packets": 0,
            },
        )
    ]

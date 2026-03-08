from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from mobilesfrdth.simulator.engine import EventDrivenEngine, Node
from mobilesfrdth.simulator.io import write_run_outputs


def _run_summary(tmp_path: pathlib.Path, *, run_id: str, n: int, mode: str) -> dict[str, float]:
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
            "speed": 1.0,
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

"""Scénario pretest_campagne/iwcmc_archive SNIR statique S7."""

from __future__ import annotations

from snir_static_common import ScenarioConfig, default_output_path, run_scenario

OUTPUT_PATH = default_output_path("S7")

CONFIG = ScenarioConfig(
    figure_id="S7",
    radius_km=3.5,
    node_counts=(450, 1350, 2700),
    packet_interval_s=300.0,
    packets_per_node=10,
    seeds=(19, 20, 21),
    pdr_targets=(0.9, 0.8, 0.7),
    output_path=OUTPUT_PATH,
)


if __name__ == "__main__":
    run_scenario(CONFIG)

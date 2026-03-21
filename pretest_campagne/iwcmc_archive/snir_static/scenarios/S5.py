"""Scénario pretest_campagne/iwcmc_archive SNIR statique S5."""

from __future__ import annotations

from snir_static_common import ScenarioConfig, default_output_path, run_scenario

OUTPUT_PATH = default_output_path("S5")

CONFIG = ScenarioConfig(
    figure_id="S5",
    radius_km=3.5,
    node_counts=(250, 750, 1500),
    packet_interval_s=900.0,
    packets_per_node=10,
    seeds=(13, 14, 15),
    pdr_targets=(0.9, 0.8, 0.7),
    output_path=OUTPUT_PATH,
)


if __name__ == "__main__":
    run_scenario(CONFIG)

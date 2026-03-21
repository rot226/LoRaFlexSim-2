"""Scénario pretest_campagne/iwcmc_archive SNIR statique S4."""

from __future__ import annotations

from snir_static_common import ScenarioConfig, default_output_path, run_scenario

OUTPUT_PATH = default_output_path("S4")

CONFIG = ScenarioConfig(
    figure_id="S4",
    radius_km=2.5,
    node_counts=(500, 1500, 3000),
    packet_interval_s=150.0,
    packets_per_node=10,
    seeds=(10, 11, 12),
    pdr_targets=(0.9, 0.8, 0.7),
    output_path=OUTPUT_PATH,
)


if __name__ == "__main__":
    run_scenario(CONFIG)

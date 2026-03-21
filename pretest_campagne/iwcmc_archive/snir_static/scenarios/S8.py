"""Scénario pretest_campagne/iwcmc_archive SNIR statique S8."""

from __future__ import annotations

from snir_static_common import ScenarioConfig, default_output_path, run_scenario

OUTPUT_PATH = default_output_path("S8")

CONFIG = ScenarioConfig(
    figure_id="S8",
    radius_km=3.5,
    node_counts=(550, 1650, 3300),
    packet_interval_s=150.0,
    packets_per_node=10,
    seeds=(22, 23, 24),
    pdr_targets=(0.9, 0.8, 0.7),
    output_path=OUTPUT_PATH,
)


if __name__ == "__main__":
    run_scenario(CONFIG)

"""Scénario pretest_campagne/iwcmc_archive SNIR statique S2."""

from __future__ import annotations

from snir_static_common import ScenarioConfig, default_output_path, run_scenario

OUTPUT_PATH = default_output_path("S2")

CONFIG = ScenarioConfig(
    figure_id="S2",
    radius_km=2.5,
    node_counts=(300, 900, 1800),
    packet_interval_s=600.0,
    packets_per_node=10,
    seeds=(4, 5, 6),
    pdr_targets=(0.9, 0.8, 0.7),
    output_path=OUTPUT_PATH,
)


if __name__ == "__main__":
    run_scenario(CONFIG)

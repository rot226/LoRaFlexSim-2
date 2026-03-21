"""Scénario pretest_campagne/iwcmc_archive SNIR statique S3."""

from __future__ import annotations

from snir_static_common import ScenarioConfig, default_output_path, run_scenario

OUTPUT_PATH = default_output_path("S3")

CONFIG = ScenarioConfig(
    figure_id="S3",
    radius_km=2.5,
    node_counts=(400, 1200, 2400),
    packet_interval_s=300.0,
    packets_per_node=10,
    seeds=(7, 8, 9),
    pdr_targets=(0.9, 0.8, 0.7),
    output_path=OUTPUT_PATH,
)


if __name__ == "__main__":
    run_scenario(CONFIG)

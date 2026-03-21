"""Manifest statique des figures attendues pour l'scenario C."""

from __future__ import annotations

from collections.abc import Iterable

EXPECTED_FIGURES_BY_STEP: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "step1": (
        ("pretest_campagne.scenario_c.step1.plots.plot_S1", ("plot_S1", "plot_S1_summary")),
        ("pretest_campagne.scenario_c.step1.plots.plot_S2", ("plot_S2",)),
        ("pretest_campagne.scenario_c.step1.plots.plot_S3", ("plot_S3",)),
        ("pretest_campagne.scenario_c.step1.plots.plot_S4", ("plot_S4", "plot_S4_summary")),
        ("pretest_campagne.scenario_c.step1.plots.plot_S5", ("plot_S5",)),
        ("pretest_campagne.scenario_c.step1.plots.plot_S6", ("plot_S6",)),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S6_cluster_pdr_vs_density",
            ("plot_S6_cluster_pdr_vs_density",),
        ),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S6_cluster_pdr_vs_network_size",
            ("plot_S6_cluster_pdr_vs_network_size",),
        ),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S7_cluster_outage_vs_density",
            ("plot_S7_cluster_outage_vs_density",),
        ),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S7_cluster_outage_vs_network_size",
            ("plot_S7_cluster_outage_vs_network_size",),
        ),
        ("pretest_campagne.scenario_c.step1.plots.plot_S8_spreading_factor_distribution", ("plot_S8",)),
        ("pretest_campagne.scenario_c.step1.plots.plot_S9_latency_or_toa_vs_network_size", ("plot_S9",)),
        ("pretest_campagne.scenario_c.step1.plots.plot_S10_rssi_cdf_by_algo", ("plot_S10",)),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S10_rssi_or_snr_cdf",
            ("plot_S10_rssi_or_snr_cdf",),
        ),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S_new1_pdr_cluster_paper",
            ("plot_S_new1_pdr_cluster_paper",),
        ),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S_new2_throughput_cluster_global",
            ("plot_S_new2_throughput_cluster_global",),
        ),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S_new3_energy_per_delivered_packet",
            ("plot_S_new3_energy_per_delivered_packet",),
        ),
        (
            "pretest_campagne.scenario_c.step1.plots.plot_S_new4_interference_realism",
            ("plot_S_new4_interference_realism",),
        ),
    ),
    "step2": (
        ("pretest_campagne.scenario_c.step2.plots.plot_RL1", ("plot_RL1",)),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_RL1_learning_curve_reward",
            ("plot_RL1_learning_curve_reward",),
        ),
        ("pretest_campagne.scenario_c.step2.plots.plot_RL2", ("plot_RL2",)),
        ("pretest_campagne.scenario_c.step2.plots.plot_RL3", ("plot_RL3",)),
        ("pretest_campagne.scenario_c.step2.plots.plot_RL4", ("plot_RL4",)),
        ("pretest_campagne.scenario_c.step2.plots.plot_RL5", ("plot_RL5",)),
        ("pretest_campagne.scenario_c.step2.plots.plot_RL5_plus", ("plot_RL5_plus",)),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_RL6_cluster_outage_vs_density",
            ("plot_RL6_cluster_outage_vs_density", "plot_RL6_cluster_outage_raw_by_replication"),
        ),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_RL7_reward_vs_density",
            ("plot_RL7_reward_vs_density",),
        ),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_RL8_reward_distribution",
            ("plot_RL8_reward_distribution",),
        ),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_RL9_sf_selection_entropy",
            ("plot_RL9_sf_selection_entropy",),
        ),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_RL10_reward_vs_pdr_scatter",
            ("plot_RL10_reward_vs_pdr_scatter",),
        ),
        ("pretest_campagne.scenario_c.step2.plots.plot_R_new1_pdr_global", ("plot_R_new1_pdr_global",)),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_R_new2_energy_per_packet",
            ("plot_R_new2_energy_per_packet",),
        ),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_R_new3_learning_curve",
            ("plot_R_new3_learning_curve",),
        ),
        ("pretest_campagne.scenario_c.step2.plots.plot_R_new4_sf_policy", ("plot_R_new4_sf_policy",)),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_R_new5_pdr_energy_tradeoff",
            ("plot_R_new5_pdr_energy_tradeoff",),
        ),
        (
            "pretest_campagne.scenario_c.step2.plots.plot_R_figure3_ucb1_vs_baselines",
            ("plot_R_figure3_ucb1_vs_baselines",),
        ),
    ),
    "post": (
        (
            "pretest_campagne.scenario_c.reproduce_author_results",
            (
                "fig4_der_by_cluster",
                "fig5_der_by_load",
                "fig7_traffic_sacrifice",
                "fig8_throughput_clusters",
            ),
        ),
        ("pretest_campagne.scenario_c.compare_with_snir", ("compare_with_snir",)),
        ("pretest_campagne.scenario_c.plot_cluster_der", ("plot_cluster_der",)),
    ),
}

EXPECTED_PNG_STEMS_BY_STEP: dict[str, tuple[str, ...]] = {
    step: tuple(stem for _, stems in modules for stem in stems)
    for step, modules in EXPECTED_FIGURES_BY_STEP.items()
}


def iter_expected_png_stems() -> Iterable[tuple[str, str]]:
    for step, stems in EXPECTED_PNG_STEMS_BY_STEP.items():
        for stem in stems:
            yield step, stem

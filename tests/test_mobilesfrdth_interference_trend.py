from __future__ import annotations

import pathlib
import random

from mobilesfrdth.simulator.channel import ChannelConfig, received_power_dbm
from mobilesfrdth.simulator.interference import InterferenceConfig, transmission_success
from mobilesfrdth.simulator.metrics import der, pdr


def _scenario_metrics(node_count: int, *, sigma_shadowing: float) -> tuple[float, float]:
    rng = random.Random(12345)
    channel_cfg = ChannelConfig(
        pathloss_exponent=2.9,
        sigma_shadowing=sigma_shadowing,
        rayleigh_fading=False,
    )
    interference_cfg = InterferenceConfig(snir_enabled=True)

    # Scénario fixe : N plus grand => charge co-SF/inter-SF plus forte.
    distances_m = [180.0 + (idx % 24) * 45.0 + (idx // 24) * 20.0 for idx in range(node_count)]
    spreading_factors = [7 + (idx % 6) for idx in range(node_count)]
    rx_powers_dbm = [
        received_power_dbm(tx_power_dbm=14.0, distance_m=dist, cfg=channel_cfg, rng=rng)
        for dist in distances_m
    ]

    delivered = 0
    for idx in range(node_count):
        interferers = [
            (rx_powers_dbm[j], spreading_factors[j])
            for j in range(node_count)
            if j != idx
        ]
        success, _ = transmission_success(
            rx_powers_dbm[idx],
            signal_sf=spreading_factors[idx],
            interferers=interferers,
            cfg=interference_cfg,
        )
        delivered += int(success)

    transmitted = node_count
    generated = int(node_count * 1.25)
    return pdr(delivered, transmitted), der(delivered, generated)


def test_snir_on_pdr_der_decrease_when_network_load_increases() -> None:
    pdr_n50, der_n50 = _scenario_metrics(node_count=50, sigma_shadowing=0.0)
    pdr_n160, der_n160 = _scenario_metrics(node_count=160, sigma_shadowing=0.0)

    assert pdr_n160 < pdr_n50
    assert der_n160 < der_n50


def test_shadowing_calibration_sigma_0_vs_6_affects_snir_on_sensitivity() -> None:
    pdr_n50_s0, der_n50_s0 = _scenario_metrics(node_count=50, sigma_shadowing=0.0)
    pdr_n160_s0, der_n160_s0 = _scenario_metrics(node_count=160, sigma_shadowing=0.0)

    pdr_n50_s6, der_n50_s6 = _scenario_metrics(node_count=50, sigma_shadowing=6.0)
    pdr_n160_s6, der_n160_s6 = _scenario_metrics(node_count=160, sigma_shadowing=6.0)

    gap_pdr_s0 = pdr_n50_s0 - pdr_n160_s0
    gap_der_s0 = der_n50_s0 - der_n160_s0
    gap_pdr_s6 = pdr_n50_s6 - pdr_n160_s6
    gap_der_s6 = der_n50_s6 - der_n160_s6

    assert gap_pdr_s0 > 0.0
    assert gap_der_s0 > 0.0
    assert gap_pdr_s6 > 0.0
    assert gap_der_s6 > 0.0

    # Le shadowing fort (sigma=6) modifie la sensibilité de la courbe charge->performance.
    assert abs(gap_pdr_s6 - gap_pdr_s0) > 1e-3
    assert abs(gap_der_s6 - gap_der_s0) > 1e-3

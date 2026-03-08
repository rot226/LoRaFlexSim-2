from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from mobilesfrdth.simulator.channel import ChannelConfig, received_power_dbm
from mobilesfrdth.simulator.interference import InterferenceConfig, transmission_success


def _scenario_pdr(node_count: int) -> float:
    channel_cfg = ChannelConfig(
        pathloss_exponent=2.9,
        sigma_shadowing=0.0,
        rayleigh_fading=False,
    )
    interference_cfg = InterferenceConfig(snir_enabled=True)

    # Scénario fixe et déterministe : N plus grand => charge co-SF/inter-SF plus forte.
    distances_m = [180.0 + (idx % 24) * 45.0 + (idx // 24) * 20.0 for idx in range(node_count)]
    spreading_factors = [7 + (idx % 6) for idx in range(node_count)]
    rx_powers_dbm = [
        received_power_dbm(tx_power_dbm=14.0, distance_m=dist, cfg=channel_cfg)
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

    return delivered / node_count


def test_pdr_trend_decreases_when_network_load_increases_snir_on() -> None:
    pdr_n50 = _scenario_pdr(node_count=50)
    pdr_n160 = _scenario_pdr(node_count=160)

    assert pdr_n160 < pdr_n50

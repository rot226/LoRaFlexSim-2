from __future__ import annotations

import pathlib

from mobilesfrdth.simulator.channel import ChannelConfig, received_power_dbm
from mobilesfrdth.simulator.interference import InterferenceConfig, transmission_success


def _pdr(node_count: int, *, snir_enabled: bool) -> float:
    channel_cfg = ChannelConfig(pathloss_exponent=2.95, sigma_shadowing=0.0, rayleigh_fading=False)
    interference_cfg = InterferenceConfig(snir_enabled=snir_enabled)

    distances_m = [170.0 + (idx % 30) * 40.0 + (idx // 30) * 30.0 for idx in range(node_count)]
    spreading_factors = [7 + (idx % 6) for idx in range(node_count)]
    rx_powers_dbm = [received_power_dbm(tx_power_dbm=14.0, distance_m=d, cfg=channel_cfg) for d in distances_m]

    delivered = 0
    for idx in range(node_count):
        interferers = [(rx_powers_dbm[j], spreading_factors[j]) for j in range(node_count) if j != idx]
        success, _ = transmission_success(
            rx_powers_dbm[idx],
            signal_sf=spreading_factors[idx],
            interferers=interferers,
            cfg=interference_cfg,
        )
        delivered += int(success)
    return delivered / node_count


def test_snir_on_degrades_pdr_vs_snir_off_under_high_load() -> None:
    pdr_off = _pdr(220, snir_enabled=False)
    pdr_on = _pdr(220, snir_enabled=True)

    assert pdr_on < pdr_off

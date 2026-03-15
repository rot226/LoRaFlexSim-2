from __future__ import annotations

import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from mobilesfrdth.simulator.channel import (
    ChannelConfig,
    channel_parameter_sanity_check,
    thermal_noise_floor_dbm,
    received_power_dbm,
)
from mobilesfrdth.simulator.interference import (
    INTER_SF_ALPHA_MATRIX,
    SNR_THRESHOLDS_DB,
    InterferenceConfig,
    transmission_success,
)
from mobilesfrdth.simulator.metrics import der, pdr


def _run_profile(
    *,
    node_count: int,
    interferer_probability: float,
    pathloss_exponent: float,
    sigma_shadowing_db: float,
    noise_figure_db: float,
    alpha_scale: float,
    snr_threshold_offset_db: float,
    density_penalty_scale: float,
    seed: int = 20260601,
) -> tuple[float, float, float]:
    rng = random.Random(seed)
    distances_m = [100.0 + (idx % 40) * 25.0 + (idx // 40) * 20.0 for idx in range(node_count)]
    spreading_factors = [7 + (idx % 6) for idx in range(node_count)]

    channel_cfg = ChannelConfig(
        pathloss_exponent=pathloss_exponent,
        sigma_shadowing=sigma_shadowing_db,
        rayleigh_fading=False,
    )
    alpha_matrix = {
        sf_i: {sf_s: min(1.0, alpha * alpha_scale) for sf_s, alpha in row.items()}
        for sf_i, row in INTER_SF_ALPHA_MATRIX.items()
    }
    snr_thresholds = {sf: threshold + snr_threshold_offset_db for sf, threshold in SNR_THRESHOLDS_DB.items()}
    interference_cfg = InterferenceConfig(
        snir_enabled=True,
        noise_floor_dbm=thermal_noise_floor_dbm(noise_figure_db=noise_figure_db),
        alpha_matrix=alpha_matrix,
        snr_thresholds_db=snr_thresholds,
        density_penalty_db_per_log=1.20 * density_penalty_scale,
        co_sf_penalty_db_per_log=1.80 * density_penalty_scale,
        inter_sf_penalty_db_per_log=0.60 * density_penalty_scale,
        max_density_penalty_db=11.0 * density_penalty_scale,
    )

    delivered = 0
    rx_powers_dbm = [received_power_dbm(14.0, distance_m=distance, cfg=channel_cfg, rng=rng) for distance in distances_m]
    for idx in range(node_count):
        interferers = []
        for jdx in range(node_count):
            if idx == jdx:
                continue
            if rng.random() < interferer_probability:
                interferers.append((rx_powers_dbm[jdx], spreading_factors[jdx]))
        success, _ = transmission_success(
            rx_powers_dbm[idx],
            signal_sf=spreading_factors[idx],
            interferers=interferers,
            cfg=interference_cfg,
        )
        delivered += int(success)

    measured_pdr = pdr(delivered, node_count)
    measured_der = der(delivered, int(node_count * 1.25))
    outage = 1.0 - measured_pdr
    return measured_pdr, measured_der, outage


def test_channel_and_interference_sanity_checks_detect_out_of_range_calibration() -> None:
    channel_cfg = ChannelConfig(pathloss_exponent=4.8, sigma_shadowing=14.0)
    interference_cfg = InterferenceConfig(
        snir_enabled=True,
        noise_floor_dbm=-102.0,
        alpha_matrix={7: {7: 1.2, 8: -0.1}},
        snr_thresholds_db={7: -12.0, 12: -30.0},
    )

    channel_warnings = channel_parameter_sanity_check(channel_cfg, noise_floor_dbm=interference_cfg.noise_floor_dbm)
    interference_warnings = interference_cfg.calibration_sanity_check()

    assert channel_warnings
    assert interference_warnings


def test_calibration_profiles_have_expected_order_of_magnitude_for_pdr_der_outage() -> None:
    low = _run_profile(
        node_count=90,
        interferer_probability=0.08,
        pathloss_exponent=2.7,
        sigma_shadowing_db=2.0,
        noise_figure_db=6.0,
        alpha_scale=0.70,
        snr_threshold_offset_db=-1.0,
        density_penalty_scale=0.65,
    )
    medium = _run_profile(
        node_count=140,
        interferer_probability=0.16,
        pathloss_exponent=2.8,
        sigma_shadowing_db=4.0,
        noise_figure_db=7.5,
        alpha_scale=1.00,
        snr_threshold_offset_db=0.0,
        density_penalty_scale=1.00,
    )
    high = _run_profile(
        node_count=220,
        interferer_probability=0.24,
        pathloss_exponent=3.0,
        sigma_shadowing_db=6.0,
        noise_figure_db=9.5,
        alpha_scale=1.30,
        snr_threshold_offset_db=1.0,
        density_penalty_scale=1.35,
    )

    low_pdr, low_der, low_outage = low
    med_pdr, med_der, med_outage = medium
    high_pdr, high_der, high_outage = high

    assert 0.45 <= low_pdr <= 0.75
    assert 0.36 <= low_der <= 0.60
    assert 0.25 <= low_outage <= 0.55

    assert 0.08 <= med_pdr <= 0.28
    assert 0.06 <= med_der <= 0.22
    assert 0.72 <= med_outage <= 0.92

    assert 0.00 <= high_pdr <= 0.08
    assert 0.00 <= high_der <= 0.06
    assert 0.92 <= high_outage <= 1.00

    assert low_pdr > med_pdr > high_pdr
    assert low_der > med_der > high_der
    assert low_outage < med_outage < high_outage

"""Modèles de canal radio pour le moteur de simulation mobilesfrdth."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random


THERMAL_NOISE_DENSITY_DBM_PER_HZ = -174.0
IMPLEMENTATION_MARGIN_DB = 2.5
PATHLOSS_EXPONENT_BOUNDS = (2.0, 4.2)
SIGMA_SHADOWING_BOUNDS_DB = (0.0, 12.0)
LORA_NOISE_FLOOR_BOUNDS_DBM = (-130.0, -105.0)


def thermal_noise_floor_dbm(*, bandwidth_hz: float = 125_000.0, noise_figure_db: float = 7.5) -> float:
    """Retourne le plancher de bruit thermique ``N0`` (dBm) pour une bande donnée."""

    effective_bw_hz = max(bandwidth_hz, 1.0)
    return THERMAL_NOISE_DENSITY_DBM_PER_HZ + 10.0 * math.log10(effective_bw_hz) + noise_figure_db


DEFAULT_LORA_NOISE_FLOOR_DBM = thermal_noise_floor_dbm()


@dataclass(frozen=True)
class ChannelConfig:
    """Paramètres des pertes radio.

    Attributes
    ----------
    reference_distance_m:
        Distance de référence ``d0`` (m).
    pathloss_at_reference_db:
        Perte à ``d0`` (dB).
    pathloss_exponent:
        Exposant log-distance ``n``.
    sigma_shadowing:
        Ecart-type du shadowing log-normal (dB).
    rayleigh_fading:
        Active un fading Rayleigh multiplicatif en puissance.
    min_distance_m:
        Distance minimale pour éviter les singularités numériques.
    """

    reference_distance_m: float = 1.0
    pathloss_at_reference_db: float = 40.0
    pathloss_exponent: float = 2.7
    sigma_shadowing: float = 4.0
    rayleigh_fading: bool = False
    min_distance_m: float = 1.0


def channel_parameter_sanity_check(cfg: ChannelConfig, *, noise_floor_dbm: float = DEFAULT_LORA_NOISE_FLOOR_DBM) -> list[str]:
    """Retourne les avertissements de calibration pour les paramètres de canal.

    Les bornes visent une calibration LoRaWAN terrestre sub-GHz standard.
    """

    warnings: list[str] = []
    min_n, max_n = PATHLOSS_EXPONENT_BOUNDS
    min_sigma, max_sigma = SIGMA_SHADOWING_BOUNDS_DB
    min_noise, max_noise = LORA_NOISE_FLOOR_BOUNDS_DBM

    if not (min_n <= cfg.pathloss_exponent <= max_n):
        warnings.append(f"pathloss_exponent hors plage [{min_n}, {max_n}] : {cfg.pathloss_exponent}")
    if not (min_sigma <= cfg.sigma_shadowing <= max_sigma):
        warnings.append(f"sigma_shadowing hors plage [{min_sigma}, {max_sigma}] dB : {cfg.sigma_shadowing}")
    if not (min_noise <= noise_floor_dbm <= max_noise):
        warnings.append(f"noise_floor_dbm hors plage [{min_noise}, {max_noise}] dBm : {noise_floor_dbm}")
    if cfg.reference_distance_m <= 0.0:
        warnings.append("reference_distance_m doit être strictement positive")
    if cfg.min_distance_m <= 0.0:
        warnings.append("min_distance_m doit être strictement positive")
    return warnings


def pathloss_log_distance_db(distance_m: float, cfg: ChannelConfig) -> float:
    """Calcule le pathloss (dB) via le modèle log-distance."""

    d = max(distance_m, cfg.min_distance_m)
    d0 = max(cfg.reference_distance_m, 1e-9)
    return cfg.pathloss_at_reference_db + 10.0 * cfg.pathloss_exponent * math.log10(d / d0)


def shadowing_lognormal_db(cfg: ChannelConfig, rng: random.Random | None = None) -> float:
    """Retourne une perturbation de shadowing gaussienne (dB)."""

    generator = rng or random
    if cfg.sigma_shadowing <= 0:
        return 0.0
    return generator.gauss(0.0, cfg.sigma_shadowing)


def rayleigh_fading_db(rng: random.Random | None = None) -> float:
    """Retourne un fading Rayleigh converti en dB (sur la puissance)."""

    generator = rng or random
    u = max(generator.random(), 1e-12)
    power_linear = -math.log(u)  # Exp(1), donc puissance Rayleigh normalisée
    return 10.0 * math.log10(power_linear)


def received_power_dbm(
    tx_power_dbm: float,
    distance_m: float,
    cfg: ChannelConfig,
    *,
    rng: random.Random | None = None,
) -> float:
    """Calcule la puissance reçue en dBm avec pathloss + shadowing + fading optionnel."""

    pl_db = pathloss_log_distance_db(distance_m=distance_m, cfg=cfg)
    shadow_db = shadowing_lognormal_db(cfg=cfg, rng=rng)
    fading_db = rayleigh_fading_db(rng=rng) if cfg.rayleigh_fading else 0.0
    return tx_power_dbm - pl_db + shadow_db + fading_db - IMPLEMENTATION_MARGIN_DB

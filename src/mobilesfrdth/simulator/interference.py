"""Modèles d'interférence et de décision de succès de trame."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping

from .channel import DEFAULT_LORA_NOISE_FLOOR_DBM

SNR_THRESHOLDS_DB: dict[int, float] = {
    # Seuils de décodage calibrés (BW125kHz) pour obtenir un comportement plus
    # contrasté entre faibles et fortes charges réseau.
    7: -6.8,
    8: -9.4,
    9: -11.7,
    10: -14.3,
    11: -16.9,
    12: -19.4,
}

INTER_SF_ALPHA_MATRIX: dict[int, dict[int, float]] = {
    # Matrice alpha(SF_i, SF_s): co-SF dominant, inter-SF partiellement
    # orthogonaux mais avec fuite croissante pour SF élevés.
    7: {7: 1.0, 8: 0.34, 9: 0.24, 10: 0.17, 11: 0.12, 12: 0.09},
    8: {7: 0.37, 8: 1.0, 9: 0.29, 10: 0.21, 11: 0.15, 12: 0.12},
    9: {7: 0.43, 8: 0.34, 9: 1.0, 10: 0.27, 11: 0.20, 12: 0.16},
    10: {7: 0.48, 8: 0.39, 9: 0.33, 10: 1.0, 11: 0.24, 12: 0.20},
    11: {7: 0.54, 8: 0.45, 9: 0.37, 10: 0.30, 11: 1.0, 12: 0.24},
    12: {7: 0.60, 8: 0.52, 9: 0.44, 10: 0.35, 11: 0.30, 12: 1.0},
}


@dataclass(frozen=True)
class InterferenceConfig:
    """Configuration SNIR/SINR."""

    snir_enabled: bool = False
    inter_sf_enabled: bool = True
    noise_floor_dbm: float = DEFAULT_LORA_NOISE_FLOOR_DBM
    density_impact_enabled: bool = True
    density_penalty_db_per_log: float = 1.05
    co_sf_penalty_db_per_log: float = 1.35
    inter_sf_penalty_db_per_log: float = 0.45
    max_density_penalty_db: float = 8.5
    snr_thresholds_db: Mapping[int, float] = field(default_factory=lambda: dict(SNR_THRESHOLDS_DB))
    alpha_matrix: Mapping[int, Mapping[int, float]] = field(default_factory=lambda: {sf_i: dict(values) for sf_i, values in INTER_SF_ALPHA_MATRIX.items()})

    def alpha(self, sf_interferer: int, sf_signal: int) -> float:
        """Retourne le coefficient d'interférence alpha(SF_i, SF_s)."""

        if sf_interferer == sf_signal:
            return 1.0
        if not self.inter_sf_enabled:
            return 0.0
        if sf_interferer in self.alpha_matrix:
            return float(self.alpha_matrix[sf_interferer].get(sf_signal, 0.0))
        return 0.0


def density_collision_penalty_db(*, signal_sf: int, interferers: list[tuple[float, int]], cfg: InterferenceConfig) -> float:
    """Pénalité empirique (dB) due à la densité et aux collisions.

    Cette pénalité encode les pertes additionnelles non captées par la seule somme
    de puissances (saturation passerelle, recouvrements partiels, collisions co-SF).
    """

    if not cfg.density_impact_enabled:
        return 0.0

    total_interferers = len(interferers)
    if total_interferers <= 0:
        return 0.0

    co_sf_interferers = sum(1 for _, sf in interferers if sf == signal_sf)
    inter_sf_interferers = max(total_interferers - co_sf_interferers, 0)
    penalty_db = (
        cfg.density_penalty_db_per_log * math.log1p(total_interferers)
        + cfg.co_sf_penalty_db_per_log * math.log1p(co_sf_interferers)
        + cfg.inter_sf_penalty_db_per_log * math.log1p(inter_sf_interferers)
    )
    return min(penalty_db, cfg.max_density_penalty_db)


def dbm_to_mw(power_dbm: float) -> float:
    return 10.0 ** (power_dbm / 10.0)


def mw_to_db(value_mw: float) -> float:
    return 10.0 * math.log10(max(value_mw, 1e-18))


def snr_db(signal_dbm: float, noise_floor_dbm: float) -> float:
    return signal_dbm - noise_floor_dbm


def sinr_db(
    signal_dbm: float,
    *,
    signal_sf: int,
    interferers: list[tuple[float, int]],
    cfg: InterferenceConfig,
) -> float:
    """Calcule ``SINR = Pr_signal / (N0 + Σ Pr_i * alpha(SF_i,SF_s))`` en dB."""

    signal_mw = dbm_to_mw(signal_dbm)
    noise_mw = dbm_to_mw(cfg.noise_floor_dbm)
    interf_mw = 0.0
    for power_i_dbm, sf_i in interferers:
        interf_mw += dbm_to_mw(power_i_dbm) * cfg.alpha(sf_interferer=sf_i, sf_signal=signal_sf)
    return mw_to_db(signal_mw / max(noise_mw + interf_mw, 1e-18))


def transmission_success(
    signal_dbm: float,
    *,
    signal_sf: int,
    interferers: list[tuple[float, int]],
    cfg: InterferenceConfig,
) -> tuple[bool, float]:
    """Décide le succès d'une trame.

    * SNIR_OFF: compare le SNR au seuil de SF.
    * SNIR_ON: compare le SINR au seuil de SF.
    """

    threshold = float(cfg.snr_thresholds_db.get(signal_sf, -20.0))
    if not cfg.snir_enabled:
        metric = snr_db(signal_dbm, cfg.noise_floor_dbm)
        return metric >= threshold, metric

    metric = sinr_db(signal_dbm, signal_sf=signal_sf, interferers=interferers, cfg=cfg)
    metric -= density_collision_penalty_db(signal_sf=signal_sf, interferers=interferers, cfg=cfg)
    return metric >= threshold, metric

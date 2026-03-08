"""Modèles d'interférence et de décision de succès de trame."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping

from .channel import DEFAULT_LORA_NOISE_FLOOR_DBM

SNR_THRESHOLDS_DB: dict[int, float] = {
    # Sensibilité LoRa typique BW125kHz (ordre de grandeur Semtech)
    7: -6.0,
    8: -9.0,
    9: -12.0,
    10: -15.0,
    11: -17.5,
    12: -20.0,
}

INTER_SF_ALPHA_MATRIX: dict[int, dict[int, float]] = {
    7: {7: 1.0, 8: 0.22, 9: 0.20, 10: 0.18, 11: 0.16, 12: 0.14},
    8: {7: 0.24, 8: 1.0, 9: 0.22, 10: 0.20, 11: 0.18, 12: 0.16},
    9: {7: 0.26, 8: 0.24, 9: 1.0, 10: 0.22, 11: 0.20, 12: 0.18},
    10: {7: 0.28, 8: 0.26, 9: 0.24, 10: 1.0, 11: 0.22, 12: 0.20},
    11: {7: 0.30, 8: 0.28, 9: 0.26, 10: 0.24, 11: 1.0, 12: 0.22},
    12: {7: 0.32, 8: 0.30, 9: 0.28, 10: 0.26, 11: 0.24, 12: 1.0},
}


@dataclass(frozen=True)
class InterferenceConfig:
    """Configuration SNIR/SINR."""

    snir_enabled: bool = False
    inter_sf_enabled: bool = True
    noise_floor_dbm: float = DEFAULT_LORA_NOISE_FLOOR_DBM
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
    return metric >= threshold, metric

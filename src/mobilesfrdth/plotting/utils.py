"""Utilitaires de visualisation pour mobilesfrdth."""

from __future__ import annotations

import math
from dataclasses import dataclass

import matplotlib.pyplot as plt


PLOT_DPI = 300

PLOT_STYLE = {
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "lines.linewidth": 1.5,
    "lines.markersize": 4,
}


@dataclass(frozen=True)
class ConfidenceInterval:
    mean: float
    low: float
    high: float
    n: int

    @property
    def half_width(self) -> float:
        return max(0.0, self.high - self.mean)


AXIS_LABELS = {
    "N": "Nombre de nœuds N [-]",
    "speed": "Vitesse [m·s⁻¹]",
    "pdr_mean": "PDR [-]",
    "der_mean": "DER [-]",
    "throughput_bps_mean": "Débit [bit·s⁻¹]",
    "jain_fairness_mean": "Indice de Jain [-]",
    "airtime_total_s_mean": "Temps d'occupation radio [s]",
    "switch_count_mean": "Nombre de changements [-]",
    "Tc_s": "Temps de convergence Tc [s]",
    "sinr_db": "SINR [dB]",
    "quantile": "Probabilité cumulée [-]",
    "sf": "Spreading Factor [-]",
    "ratio": "Part d'utilisation [%]",
}


def setup_plot_style() -> None:
    plt.rcParams.update(PLOT_STYLE)


def normalized_axis_label(name: str) -> str:
    return AXIS_LABELS.get(name, name)


def ci95_from_samples(samples: list[float]) -> ConfidenceInterval | None:
    if not samples:
        return None
    n = len(samples)
    mean = sum(samples) / n
    if n == 1:
        return ConfidenceInterval(mean=mean, low=mean, high=mean, n=1)
    variance = sum((value - mean) ** 2 for value in samples) / (n - 1)
    std = math.sqrt(max(0.0, variance))
    half_width = 1.96 * (std / math.sqrt(n))
    return ConfidenceInterval(mean=mean, low=mean - half_width, high=mean + half_width, n=n)

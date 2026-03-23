"""Utilitaires de visualisation pour mobilesfrdth."""

from __future__ import annotations

import math
from dataclasses import dataclass

import matplotlib.pyplot as plt


PLOT_DPI = 300

UNIFIED_PLOT_STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.prop_cycle": plt.cycler(
        color=[
            "#0072B2",  # blue
            "#E69F00",  # orange
            "#009E73",  # green
            "#D55E00",  # vermillion
            "#CC79A7",  # purple
            "#56B4E9",  # light blue
            "#F0E442",  # yellow
            "#000000",  # black
        ]
    ),
    "axes.edgecolor": "#2E2E2E",
    "axes.linewidth": 0.8,
    "grid.color": "#BDBDBD",
    "grid.linestyle": "--",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.55,
    "lines.linewidth": 1.8,
    "lines.markersize": 4.5,
    "patch.linewidth": 0.8,
    "figure.dpi": PLOT_DPI,
    "savefig.dpi": PLOT_DPI,
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


def setup_plot_style(*, ieee_ready: bool = False) -> None:
    _ = ieee_ready
    plt.rcParams.update(UNIFIED_PLOT_STYLE)


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

"""Métriques agrégées propres aux campagnes de brouillage."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class JammingMetrics:
    """Résumé de l'impact du brouillage."""

    jammed_packets: int = 0
    total_packets: int = 0
    mean_jammer_power_dbm: float | None = None

    @property
    def jammed_ratio(self) -> float:
        return 0.0 if self.total_packets <= 0 else self.jammed_packets / self.total_packets


def summarize_jamming(*, jammed_flags: list[bool], jammer_powers_dbm: list[float] | None = None) -> JammingMetrics:
    """Agrège des indicateurs événementiels en métriques de campagne."""

    powers = jammer_powers_dbm or []
    return JammingMetrics(sum(1 for flag in jammed_flags if flag), len(jammed_flags), mean(powers) if powers else None)

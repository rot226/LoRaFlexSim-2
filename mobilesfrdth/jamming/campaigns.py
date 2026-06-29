"""Construction de campagnes de brouillage reproductibles."""

from __future__ import annotations

from dataclasses import dataclass

from .placement import grid_placement, random_placement
from .scenarios import JammingScenario


@dataclass(frozen=True)
class JammingCampaign:
    """Collection nommée de scénarios de brouillage."""

    name: str
    scenarios: tuple[JammingScenario, ...]


def build_campaign(*, name: str, jammer_counts: tuple[int, ...], area_size_m: float, placement: str = "grid", seed: int | None = None) -> JammingCampaign:
    """Crée une campagne en variant le nombre de brouilleurs."""

    scenarios: list[JammingScenario] = []
    for count in jammer_counts:
        if placement == "random":
            configs = random_placement(count=count, area_size_m=area_size_m, seed=None if seed is None else seed + count)
        elif placement == "grid":
            configs = grid_placement(count=count, area_size_m=area_size_m)
        else:
            raise ValueError("placement doit valoir 'grid' ou 'random'.")
        scenarios.append(JammingScenario(name=f"{name}_jammers_{count}", jammers=tuple(configs), metadata={"placement": placement}))
    return JammingCampaign(name=name, scenarios=tuple(scenarios))

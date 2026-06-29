"""Construction de campagnes de brouillage reproductibles."""

from __future__ import annotations

from dataclasses import dataclass

from .placement import circle_placement, grid_placement, random_placement
from .scenarios import JammingScenario


@dataclass(frozen=True)
class JammingCampaign:
    """Collection nommée de scénarios de brouillage."""

    name: str
    scenarios: tuple[JammingScenario, ...]


def build_campaign(
    *,
    name: str,
    jammer_counts: tuple[int, ...],
    area_size_m: float,
    placement: str = "grid",
    seed: int | None = None,
    gateway_x: float | None = None,
    gateway_y: float | None = None,
    jammer_radius_m: float = 10.0,
    start_angle_deg: float = 0.0,
) -> JammingCampaign:
    """Crée une campagne en variant le nombre de brouilleurs."""

    scenarios: list[JammingScenario] = []
    for count in jammer_counts:
        if placement == "random":
            configs = random_placement(count=count, area_size_m=area_size_m, seed=None if seed is None else seed + count)
        elif placement == "grid":
            configs = grid_placement(count=count, area_size_m=area_size_m)
        elif placement == "circle":
            center_x = area_size_m / 2 if gateway_x is None else gateway_x
            center_y = area_size_m / 2 if gateway_y is None else gateway_y
            configs = circle_placement(
                gateway_x=center_x,
                gateway_y=center_y,
                radius_m=jammer_radius_m,
                count=count,
                start_angle_deg=start_angle_deg,
            )
        else:
            raise ValueError("placement doit valoir 'grid', 'random' ou 'circle'.")
        scenarios.append(
            JammingScenario(
                name=f"{name}_jammers_{count}",
                jammers=tuple(configs),
                metadata={"placement": placement},
            )
        )
    return JammingCampaign(name=name, scenarios=tuple(scenarios))

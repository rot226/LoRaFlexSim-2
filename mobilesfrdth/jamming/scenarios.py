"""Scénarios de brouillage composables avec les campagnes mobilesfrdth."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .jammer import JammerConfig
from .placement import circle_placement


@dataclass(frozen=True)
class JammingScenario:
    """Description stable d'une extension de scénario avec brouilleurs."""

    name: str
    jammers: tuple[JammerConfig, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "jammers": [j.__dict__ for j in self.jammers],
            "metadata": dict(self.metadata),
        }


def no_jamming_scenario() -> JammingScenario:
    """Scénario témoin sans brouillage."""

    return JammingScenario(name="no_jamming")


def circle_static_jamming_scenario(
    *,
    gateway_x: float,
    gateway_y: float,
    radius_m: float = 10.0,
    number_of_jammers: int = 6,
    start_angle_deg: float = 0.0,
) -> JammingScenario:
    """Scénario avec brouilleurs statiques placés en cercle autour de la gateway."""

    return JammingScenario(
        name="circle_static_jamming",
        jammers=tuple(
            circle_placement(
                gateway_x=gateway_x,
                gateway_y=gateway_y,
                radius_m=radius_m,
                count=number_of_jammers,
                start_angle_deg=start_angle_deg,
            )
        ),
        metadata={
            "placement": "circle",
            "radius_m": radius_m,
            "start_angle_deg": start_angle_deg,
        },
    )


def circle_shifted_jamming_scenario(
    *,
    gateway_x: float,
    gateway_y: float,
    radius_m: float = 10.0,
    number_of_jammers: int = 6,
    start_angle_deg: float = 30.0,
) -> JammingScenario:
    """Scénario circulaire décalé pour comparer deux anneaux de brouilleurs."""

    return JammingScenario(
        name="circle_shifted_jamming",
        jammers=tuple(
            circle_placement(
                gateway_x=gateway_x,
                gateway_y=gateway_y,
                radius_m=radius_m,
                count=number_of_jammers,
                start_angle_deg=start_angle_deg,
            )
        ),
        metadata={
            "placement": "circle",
            "radius_m": radius_m,
            "start_angle_deg": start_angle_deg,
        },
    )

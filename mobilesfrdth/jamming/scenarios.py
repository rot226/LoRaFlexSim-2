"""Scénarios de brouillage composables avec les campagnes mobilesfrdth."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .jammer import JammerConfig


@dataclass(frozen=True)
class JammingScenario:
    """Description stable d'une extension de scénario avec brouilleurs."""

    name: str
    jammers: tuple[JammerConfig, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "jammers": [j.__dict__ for j in self.jammers], "metadata": dict(self.metadata)}


def no_jamming_scenario() -> JammingScenario:
    """Scénario témoin sans brouillage."""

    return JammingScenario(name="no_jamming")

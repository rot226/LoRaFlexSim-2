"""Modèle minimal de brouilleur LoRa pour les campagnes mobilesfrdth."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable

from mobilesfrdth.simulator.channel import ChannelConfig, received_power_dbm


@dataclass(frozen=True)
class JammerConfig:
    """Configuration radio d'un brouilleur."""

    jammer_id: str
    x_m: float
    y_m: float
    tx_power_dbm: float = 14.0
    channels_hz: tuple[int, ...] = (868_100_000,)
    duty_cycle: float = 1.0
    active: bool = True


@dataclass(frozen=True)
class JammerObservation:
    """Contribution d'un brouilleur observée par un récepteur."""

    jammer_id: str
    channel_hz: int
    distance_m: float
    power_dbm: float


class Jammer:
    """Adaptateur public stable représentant un brouilleur ponctuel."""

    def __init__(self, config: JammerConfig) -> None:
        self.config = config

    def is_active(self, time_s: float, *, rng: random.Random | None = None) -> bool:
        """Indique si le brouilleur émet à ``time_s`` selon son duty-cycle."""

        if not self.config.active:
            return False
        duty_cycle = min(max(self.config.duty_cycle, 0.0), 1.0)
        if duty_cycle >= 1.0:
            return True
        if duty_cycle <= 0.0:
            return False
        generator = rng or random
        return generator.random() < duty_cycle

    def distance_to(self, x_m: float, y_m: float) -> float:
        """Retourne la distance euclidienne entre le brouilleur et un point."""

        return math.hypot(self.config.x_m - x_m, self.config.y_m - y_m)

    def received_power_dbm(
        self,
        *,
        receiver_x_m: float,
        receiver_y_m: float,
        channel: ChannelConfig | None = None,
        rng: random.Random | None = None,
    ) -> float:
        """Calcule la puissance reçue du brouilleur au point cible."""

        cfg = channel or ChannelConfig()
        return received_power_dbm(self.config.tx_power_dbm, self.distance_to(receiver_x_m, receiver_y_m), cfg, rng=rng)

    def observations_for(
        self,
        *,
        receiver_x_m: float,
        receiver_y_m: float,
        time_s: float,
        channel: ChannelConfig | None = None,
        rng: random.Random | None = None,
    ) -> list[JammerObservation]:
        """Retourne les observations par canal si le brouilleur est actif."""

        if not self.is_active(time_s, rng=rng):
            return []
        distance = self.distance_to(receiver_x_m, receiver_y_m)
        power = received_power_dbm(self.config.tx_power_dbm, distance, channel or ChannelConfig(), rng=rng)
        return [JammerObservation(self.config.jammer_id, channel_hz, distance, power) for channel_hz in self.config.channels_hz]


def build_jammers(configs: Iterable[JammerConfig]) -> list[Jammer]:
    """Construit une liste de brouilleurs à partir de configurations immuables."""

    return [Jammer(config) for config in configs]

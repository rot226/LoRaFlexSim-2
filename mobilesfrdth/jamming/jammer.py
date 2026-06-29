"""Modèles de brouilleurs LoRa pour les campagnes mobilesfrdth."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Literal, Protocol

from mobilesfrdth.simulator.channel import ChannelConfig, received_power_dbm

TrafficTargetingMode = Literal["random", "traffic_peak", "reactive", "intelligent", "ml_based"]
SUPPORTED_TRAFFIC_TARGETING_MODES: tuple[str, ...] = ("random", "traffic_peak", "reactive", "intelligent", "ml_based")
FUNCTIONAL_TRAFFIC_TARGETING_MODES: tuple[str, ...] = ("random", "traffic_peak")
MAX_REGULATORY_DUTY_CYCLE = 0.01


class RandomLike(Protocol):
    """Interface minimale attendue pour les générateurs pseudo-aléatoires."""

    def random(self) -> float: ...

    def uniform(self, a: float, b: float) -> float: ...


@dataclass(frozen=True)
class JammingEvent:
    """Fenêtre événementielle d'émission d'un brouilleur."""

    jammer_id: str
    time_s: float
    duration_s: float
    sf: int
    frequency_mhz: float
    tx_power_dbm: float


@dataclass(frozen=True)
class JammerNode:
    """Nœud brouilleur configurable avec ordonnancement par duty-cycle."""

    jammer_id: str
    spreading_factor: int
    tx_power_dbm: float
    frequency_mhz: float
    bandwidth_khz: float
    duty_cycle: float
    position_x: float
    position_y: float
    synchronized: bool
    traffic_targeting_mode: TrafficTargetingMode

    def schedule_transmissions(self, sim_time_s: float, airtime_s: float, rng: RandomLike | None = None) -> list[JammingEvent]:
        """Planifie des fenêtres de brouillage sans dépasser ``duty_cycle * sim_time_s``.

        Les modes ``random`` et ``traffic_peak`` sont fonctionnels. Les modes
        ``reactive``, ``intelligent`` et ``ml_based`` sont réservés à de futures
        stratégies et lèvent explicitement ``NotImplementedError``.
        """

        if self.traffic_targeting_mode not in SUPPORTED_TRAFFIC_TARGETING_MODES:
            raise ValueError(f"Mode de ciblage inconnu: {self.traffic_targeting_mode!r}.")
        if self.traffic_targeting_mode not in FUNCTIONAL_TRAFFIC_TARGETING_MODES:
            raise NotImplementedError(f"Le mode {self.traffic_targeting_mode!r} est prévu mais pas encore fonctionnel.")
        if sim_time_s <= 0 or airtime_s <= 0:
            return []

        budget_s = max(0.0, min(self.duty_cycle, 1.0) * sim_time_s)
        transmission_count = int(budget_s // airtime_s)
        if transmission_count <= 0:
            return []

        generator = rng or random.Random()
        if self.traffic_targeting_mode == "traffic_peak":
            start_times = self._traffic_peak_start_times(sim_time_s, airtime_s, transmission_count, generator)
        else:
            start_times = self._random_start_times(sim_time_s, airtime_s, transmission_count, generator)

        return [
            JammingEvent(
                jammer_id=self.jammer_id,
                time_s=start,
                duration_s=airtime_s,
                sf=self.spreading_factor,
                frequency_mhz=self.frequency_mhz,
                tx_power_dbm=self.tx_power_dbm,
            )
            for start in start_times
        ]

    def validate_duty_cycle(self, sim_time_s: float, transmissions: Iterable[JammingEvent]) -> None:
        """Vérifie que le temps d'émission cumulé ne dépasse pas 1 % de la simulation."""

        if sim_time_s <= 0:
            raise ValueError("sim_time_s doit être strictement positif pour valider le duty-cycle.")
        total_airtime_s = sum(event.duration_s for event in transmissions if event.jammer_id == self.jammer_id)
        allowed_airtime_s = MAX_REGULATORY_DUTY_CYCLE * sim_time_s
        if total_airtime_s > allowed_airtime_s:
            raise ValueError(
                f"Duty-cycle réglementaire dépassé pour {self.jammer_id}: "
                f"{total_airtime_s:.6f}s > {allowed_airtime_s:.6f}s (1 % de {sim_time_s:.6f}s)."
            )

    def _random_start_times(self, sim_time_s: float, airtime_s: float, count: int, rng: RandomLike) -> list[float]:
        latest_start_s = max(0.0, sim_time_s - airtime_s)
        return sorted(rng.uniform(0.0, latest_start_s) for _ in range(count))

    def _traffic_peak_start_times(self, sim_time_s: float, airtime_s: float, count: int, rng: RandomLike) -> list[float]:
        latest_start_s = max(0.0, sim_time_s - airtime_s)
        if count == 1:
            return [0.0 if self.synchronized else rng.uniform(0.0, latest_start_s)]

        peak_center_s = 0.5 * sim_time_s
        peak_span_s = min(latest_start_s, max(airtime_s, 0.2 * sim_time_s))
        peak_start_s = max(0.0, peak_center_s - peak_span_s / 2.0)
        spacing_s = peak_span_s / max(1, count - 1)
        starts: list[float] = []
        for index in range(count):
            jitter_s = 0.0 if self.synchronized else rng.uniform(-0.25 * spacing_s, 0.25 * spacing_s)
            starts.append(min(latest_start_s, max(0.0, peak_start_s + index * spacing_s + jitter_s)))
        return sorted(starts)


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

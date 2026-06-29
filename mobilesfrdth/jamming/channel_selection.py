"""Sélection de canaux pour les scénarios de brouillage et de mobilité.

La politique ``adr-assisted`` est une option expérimentale propre à ce
simulateur. Elle exploite des informations ADR déjà présentes dans l'état du
nœud ou dans le contexte de simulation pour orienter le choix de canal, mais
elle ne représente pas un comportement automatique de l'ADR LoRaWAN standard :
LoRaWAN ADR ajuste notamment le data rate et la puissance d'émission, pas une
migration de canal imposée par la norme.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random
from typing import Any, Iterable, Mapping, Protocol

EU868_DEFAULT_CHANNELS_MHZ = [868.1, 868.3, 868.5, 867.1, 867.3, 867.5, 867.7, 867.9]
DEFAULT_LORAWAN_CHANNELS_HZ: tuple[int, ...] = tuple(int(freq * 1_000_000) for freq in EU868_DEFAULT_CHANNELS_MHZ[:3])


class RandomLike(Protocol):
    """Interface minimale acceptée pour les générateurs pseudo-aléatoires."""

    def randrange(self, stop: int) -> int: ...

    def choice(self, seq: list[float]) -> float: ...


@dataclass(frozen=True)
class ChannelSet:
    """Ensemble ordonné de canaux exprimés en MHz."""

    frequencies_mhz: list[float]

    def __post_init__(self) -> None:
        if not self.frequencies_mhz:
            raise ValueError("La liste de fréquences ne peut pas être vide.")
        object.__setattr__(self, "frequencies_mhz", [float(freq) for freq in self.frequencies_mhz])

    def channel_id_for_frequency(self, frequency_mhz: float, *, tolerance_mhz: float = 1e-6) -> int:
        """Retourne l'identifiant ordinal du canal correspondant à ``frequency_mhz``.

        Les identifiants sont indexés à partir de zéro selon l'ordre de
        ``frequencies_mhz``. Une petite tolérance évite les faux négatifs dus
        aux représentations flottantes.
        """

        target = float(frequency_mhz)
        for index, frequency in enumerate(self.frequencies_mhz):
            if abs(frequency - target) <= tolerance_mhz:
                return index
        raise ValueError(f"Fréquence inconnue dans cet ensemble de canaux: {frequency_mhz!r} MHz.")


class ChannelSelectionPolicy(ABC):
    """Classe de base des politiques de sélection de canal."""

    name: str = "base"
    requires_adr_or_override: bool = False

    @abstractmethod
    def select_channel(
        self,
        node_state: Any,
        available_channels: ChannelSet | Iterable[float],
        rng: RandomLike | random.Random,
        context: Mapping[str, Any] | Any | None = None,
    ) -> float:
        """Sélectionne une fréquence en MHz pour ``node_state``."""

    def _validate_selection(self, selected: float, node_state: Any, context: Mapping[str, Any] | Any | None) -> float:
        if self.requires_adr_or_override and not _adr_enabled(node_state, context) and not _allow_without_adr(context):
            raise PermissionError(
                f"La politique {self.name!r} nécessite ADR ou allow_channel_selection_without_adr=True."
            )
        current = _current_frequency_mhz(node_state)
        if current is not None and abs(float(selected) - current) > 1e-6:
            if not _adr_enabled(node_state, context) and not _allow_without_adr(context):
                raise PermissionError("Les migrations de canal nécessitent ADR ou allow_channel_selection_without_adr=True.")
        return float(selected)


class StaticChannelSelectionPolicy(ChannelSelectionPolicy):
    """Conserve le canal courant, ou le premier canal disponible à l'initialisation."""

    name = "static"

    def select_channel(self, node_state: Any, available_channels: ChannelSet | Iterable[float], rng: RandomLike | random.Random, context: Mapping[str, Any] | Any | None = None) -> float:
        channels = _as_channel_set(available_channels)
        current = _current_frequency_mhz(node_state)
        selected = current if current in channels.frequencies_mhz else channels.frequencies_mhz[0]
        return self._validate_selection(selected, node_state, context)


class RandomChannelSelectionPolicy(ChannelSelectionPolicy):
    """Choisit uniformément un canal disponible."""

    name = "random"

    def select_channel(self, node_state: Any, available_channels: ChannelSet | Iterable[float], rng: RandomLike | random.Random, context: Mapping[str, Any] | Any | None = None) -> float:
        channels = _as_channel_set(available_channels)
        selected = rng.choice(channels.frequencies_mhz) if hasattr(rng, "choice") else channels.frequencies_mhz[rng.randrange(len(channels.frequencies_mhz))]
        return self._validate_selection(selected, node_state, context)


class AdrAssistedChannelSelectionPolicy(ChannelSelectionPolicy):
    """Politique expérimentale assistée par ADR, non standard LoRaWAN."""

    name = "adr-assisted"
    requires_adr_or_override = True

    def select_channel(self, node_state: Any, available_channels: ChannelSet | Iterable[float], rng: RandomLike | random.Random, context: Mapping[str, Any] | Any | None = None) -> float:
        channels = _as_channel_set(available_channels)
        candidate = _first_value(node_state, context, "adr_frequency_mhz", "recommended_frequency_mhz", "best_frequency_mhz")
        if candidate is None:
            candidate_id = _first_value(node_state, context, "adr_channel_id", "recommended_channel_id", "best_channel_id")
            if candidate_id is not None:
                candidate = channels.frequencies_mhz[int(candidate_id) % len(channels.frequencies_mhz)]
        selected = float(candidate) if candidate in channels.frequencies_mhz else channels.frequencies_mhz[0]
        return self._validate_selection(selected, node_state, context)


class DegradationAwareChannelSelectionPolicy(ChannelSelectionPolicy):
    """Privilégie le canal le moins dégradé selon le contexte fourni."""

    name = "degradation-aware"

    def select_channel(self, node_state: Any, available_channels: ChannelSet | Iterable[float], rng: RandomLike | random.Random, context: Mapping[str, Any] | Any | None = None) -> float:
        channels = _as_channel_set(available_channels)
        degradation = _get(context, "channel_degradation") or _get(context, "degradation_by_frequency_mhz") or {}
        quality = _get(context, "channel_quality") or _get(context, "quality_by_frequency_mhz") or {}

        def score(freq: float) -> tuple[float, float]:
            return (float(quality.get(freq, quality.get(str(freq), 0.0))), -float(degradation.get(freq, degradation.get(str(freq), 0.0))))

        selected = max(channels.frequencies_mhz, key=score)
        return self._validate_selection(selected, node_state, context)


POLICIES: dict[str, type[ChannelSelectionPolicy]] = {
    "static": StaticChannelSelectionPolicy,
    "random": RandomChannelSelectionPolicy,
    "adr-assisted": AdrAssistedChannelSelectionPolicy,
    "degradation-aware": DegradationAwareChannelSelectionPolicy,
}


def build_channel_selection_policy(name: str) -> ChannelSelectionPolicy:
    """Construit une politique de sélection par nom."""

    try:
        return POLICIES[name]()
    except KeyError as exc:
        raise ValueError(f"Politique de sélection de canal inconnue: {name!r}.") from exc


def fixed_channels(channels_hz: tuple[int, ...] | None = None) -> tuple[int, ...]:
    """Retourne les canaux fournis ou les canaux LoRaWAN EU868 par défaut."""
    return tuple(channels_hz or DEFAULT_LORAWAN_CHANNELS_HZ)


def round_robin_channel(index: int, channels_hz: tuple[int, ...] | None = None) -> int:
    channels = fixed_channels(channels_hz)
    if not channels:
        raise ValueError("La liste de canaux ne peut pas être vide.")
    return channels[index % len(channels)]


def random_channel(*, seed: int | None = None, channels_hz: tuple[int, ...] | None = None) -> int:
    channels = fixed_channels(channels_hz)
    if not channels:
        raise ValueError("La liste de canaux ne peut pas être vide.")
    return random.Random(seed).choice(channels)


def _as_channel_set(channels: ChannelSet | Iterable[float]) -> ChannelSet:
    return channels if isinstance(channels, ChannelSet) else ChannelSet(list(channels))


def _get(source: Mapping[str, Any] | Any | None, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _first_value(node_state: Any, context: Mapping[str, Any] | Any | None, *keys: str) -> Any:
    for key in keys:
        value = _get(node_state, key, None)
        if value is not None:
            return value
        value = _get(context, key, None)
        if value is not None:
            return value
    return None


def _adr_enabled(node_state: Any, context: Mapping[str, Any] | Any | None) -> bool:
    value = _first_value(node_state, context, "adr_enabled", "adr")
    return True if value is None else bool(value)


def _allow_without_adr(context: Mapping[str, Any] | Any | None) -> bool:
    return bool(_get(context, "allow_channel_selection_without_adr", False))


def _current_frequency_mhz(node_state: Any) -> float | None:
    for key in ("frequency_mhz", "current_frequency_mhz"):
        value = _get(node_state, key, None)
        if value is not None:
            return float(value)
    value = _get(node_state, "frequency_hz", None) or _get(node_state, "current_frequency_hz", None)
    return None if value is None else float(value) / 1_000_000.0

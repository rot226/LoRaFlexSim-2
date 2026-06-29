"""Sélection de canaux ciblés par les brouilleurs."""

from __future__ import annotations

import random

DEFAULT_LORAWAN_CHANNELS_HZ: tuple[int, ...] = (868_100_000, 868_300_000, 868_500_000)


def fixed_channels(channels_hz: tuple[int, ...] | None = None) -> tuple[int, ...]:
    """Retourne les canaux fournis ou les canaux LoRaWAN EU868 par défaut."""

    return tuple(channels_hz or DEFAULT_LORAWAN_CHANNELS_HZ)


def round_robin_channel(index: int, channels_hz: tuple[int, ...] | None = None) -> int:
    """Sélectionne un canal par index circulaire."""

    channels = fixed_channels(channels_hz)
    if not channels:
        raise ValueError("La liste de canaux ne peut pas être vide.")
    return channels[index % len(channels)]


def random_channel(*, seed: int | None = None, channels_hz: tuple[int, ...] | None = None) -> int:
    """Sélectionne un canal pseudo-aléatoire reproductible."""

    channels = fixed_channels(channels_hz)
    if not channels:
        raise ValueError("La liste de canaux ne peut pas être vide.")
    return random.Random(seed).choice(channels)

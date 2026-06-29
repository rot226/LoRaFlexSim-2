"""Placement déterministe de brouilleurs dans une zone carrée."""

from __future__ import annotations

import math
import random

from .jammer import JammerConfig


def grid_placement(*, count: int, area_size_m: float, tx_power_dbm: float = 14.0, channels_hz: tuple[int, ...] = (868_100_000,)) -> list[JammerConfig]:
    """Place ``count`` brouilleurs sur une grille régulière."""

    if count < 0 or area_size_m <= 0:
        raise ValueError("count doit être >= 0 et area_size_m > 0.")
    side = max(1, math.ceil(math.sqrt(count)))
    step = area_size_m / (side + 1)
    configs: list[JammerConfig] = []
    for idx in range(count):
        row, col = divmod(idx, side)
        configs.append(JammerConfig(f"jammer-{idx+1}", (col + 1) * step, (row + 1) * step, tx_power_dbm, channels_hz))
    return configs


def random_placement(*, count: int, area_size_m: float, seed: int | None = None, tx_power_dbm: float = 14.0, channels_hz: tuple[int, ...] = (868_100_000,)) -> list[JammerConfig]:
    """Place ``count`` brouilleurs uniformément dans la zone."""

    if count < 0 or area_size_m <= 0:
        raise ValueError("count doit être >= 0 et area_size_m > 0.")
    rng = random.Random(seed)
    return [JammerConfig(f"jammer-{idx+1}", rng.uniform(0, area_size_m), rng.uniform(0, area_size_m), tx_power_dbm, channels_hz) for idx in range(count)]

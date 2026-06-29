"""Placement déterministe de brouilleurs."""

from __future__ import annotations

import math
import random

from .jammer import JammerConfig


def place_jammers_on_circle(
    gateway_x: float,
    gateway_y: float,
    radius_m: float = 10.0,
    number_of_jammers: int = 6,
    start_angle_deg: float = 0.0,
) -> list[tuple[float, float, float]]:
    """Retourne des positions de brouilleurs régulièrement espacées sur un cercle.

    Les angles sont exprimés en degrés et progressent dans l'ordre trigonométrique
    à partir de ``start_angle_deg``. Chaque position retournée contient
    ``(x, y, angle_deg)`` et se trouve à ``radius_m`` de la gateway.
    """

    if radius_m < 0:
        raise ValueError("radius_m doit être >= 0.")
    if number_of_jammers <= 0:
        raise ValueError("number_of_jammers doit être > 0.")

    spacing_deg = 360.0 / number_of_jammers
    positions: list[tuple[float, float, float]] = []
    for index in range(number_of_jammers):
        angle_deg = start_angle_deg + index * spacing_deg
        angle_rad = math.radians(angle_deg)
        x_m = gateway_x + radius_m * math.cos(angle_rad)
        y_m = gateway_y + radius_m * math.sin(angle_rad)

        distance_m = math.hypot(x_m - gateway_x, y_m - gateway_y)
        if not math.isclose(distance_m, radius_m, rel_tol=1e-12, abs_tol=1e-9):
            raise ArithmeticError(
                "Le placement circulaire a produit un point hors tolérance."
            )
        positions.append((x_m, y_m, angle_deg))
    return positions


def circle_placement(
    *,
    gateway_x: float,
    gateway_y: float,
    radius_m: float = 10.0,
    count: int = 6,
    start_angle_deg: float = 0.0,
    tx_power_dbm: float = 14.0,
    channels_hz: tuple[int, ...] = (868_100_000,),
) -> list[JammerConfig]:
    """Place ``count`` brouilleurs sur un cercle centré sur la gateway."""

    positions = place_jammers_on_circle(
        gateway_x,
        gateway_y,
        radius_m=radius_m,
        number_of_jammers=count,
        start_angle_deg=start_angle_deg,
    )
    return [
        JammerConfig(f"jammer-{idx + 1}", x_m, y_m, tx_power_dbm, channels_hz)
        for idx, (x_m, y_m, _angle_deg) in enumerate(positions)
    ]


def grid_placement(
    *,
    count: int,
    area_size_m: float,
    tx_power_dbm: float = 14.0,
    channels_hz: tuple[int, ...] = (868_100_000,),
) -> list[JammerConfig]:
    """Place ``count`` brouilleurs sur une grille régulière."""

    if count < 0 or area_size_m <= 0:
        raise ValueError("count doit être >= 0 et area_size_m > 0.")
    side = max(1, math.ceil(math.sqrt(count)))
    step = area_size_m / (side + 1)
    configs: list[JammerConfig] = []
    for idx in range(count):
        row, col = divmod(idx, side)
        configs.append(
            JammerConfig(
                f"jammer-{idx + 1}",
                (col + 1) * step,
                (row + 1) * step,
                tx_power_dbm,
                channels_hz,
            )
        )
    return configs


def random_placement(
    *,
    count: int,
    area_size_m: float,
    seed: int | None = None,
    tx_power_dbm: float = 14.0,
    channels_hz: tuple[int, ...] = (868_100_000,),
) -> list[JammerConfig]:
    """Place ``count`` brouilleurs uniformément dans la zone."""

    if count < 0 or area_size_m <= 0:
        raise ValueError("count doit être >= 0 et area_size_m > 0.")
    rng = random.Random(seed)
    return [
        JammerConfig(
            f"jammer-{idx + 1}",
            rng.uniform(0, area_size_m),
            rng.uniform(0, area_size_m),
            tx_power_dbm,
            channels_hz,
        )
        for idx in range(count)
    ]

from __future__ import annotations

import math

import pytest

from mobilesfrdth.jamming import place_jammers_on_circle


def test_six_jammers_are_placed_ten_meters_apart_every_sixty_degrees() -> None:
    positions = place_jammers_on_circle(100.0, 200.0, radius_m=10.0)

    assert len(positions) == 6
    assert [angle for _x, _y, angle in positions] == pytest.approx(
        [0.0, 60.0, 120.0, 180.0, 240.0, 300.0]
    )
    for x_m, y_m, _angle_deg in positions:
        assert math.hypot(x_m - 100.0, y_m - 200.0) == pytest.approx(10.0, abs=1e-9)

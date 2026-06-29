from __future__ import annotations

import math

import pytest

from mobilesfrdth.jamming import (
    build_campaign,
    circle_shifted_jamming_scenario,
    circle_static_jamming_scenario,
    place_jammers_on_circle,
)


def test_place_jammers_on_circle_returns_ordered_sixty_degree_positions() -> None:
    positions = place_jammers_on_circle(100.0, 200.0, radius_m=10.0)

    assert [angle for _x, _y, angle in positions] == pytest.approx(
        [0.0, 60.0, 120.0, 180.0, 240.0, 300.0]
    )
    for x_m, y_m, _angle in positions:
        assert math.hypot(x_m - 100.0, y_m - 200.0) == pytest.approx(10.0, abs=1e-9)


def test_circle_jamming_scenarios_reuse_circle_placement() -> None:
    static = circle_static_jamming_scenario(gateway_x=0.0, gateway_y=0.0)
    shifted = circle_shifted_jamming_scenario(gateway_x=0.0, gateway_y=0.0)

    assert len(static.jammers) == 6
    assert len(shifted.jammers) == 6
    assert static.metadata["placement"] == "circle"
    assert shifted.metadata["placement"] == "circle"
    assert (static.jammers[0].x_m, static.jammers[0].y_m) == pytest.approx((10.0, 0.0))
    assert (shifted.jammers[0].x_m, shifted.jammers[0].y_m) == pytest.approx(
        (10.0 * math.cos(math.radians(30.0)), 10.0 * math.sin(math.radians(30.0)))
    )


def test_build_campaign_can_generate_circle_jamming_scenarios() -> None:
    campaign = build_campaign(
        name="circle",
        jammer_counts=(6,),
        area_size_m=100.0,
        placement="circle",
        gateway_x=25.0,
        gateway_y=75.0,
        jammer_radius_m=10.0,
    )

    scenario = campaign.scenarios[0]
    assert scenario.metadata["placement"] == "circle"
    assert len(scenario.jammers) == 6
    for jammer in scenario.jammers:
        assert math.hypot(jammer.x_m - 25.0, jammer.y_m - 75.0) == pytest.approx(10.0, abs=1e-9)

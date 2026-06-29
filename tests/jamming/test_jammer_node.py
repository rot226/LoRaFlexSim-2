from __future__ import annotations

import random

import pytest

from mobilesfrdth.jamming.jammer import JammingEvent, JammerNode


def make_node(**overrides) -> JammerNode:
    values = {
        "jammer_id": "jammer-1",
        "spreading_factor": 7,
        "tx_power_dbm": 14.0,
        "frequency_mhz": 868.1,
        "bandwidth_khz": 125.0,
        "duty_cycle": 0.01,
        "position_x": 10.0,
        "position_y": 20.0,
        "synchronized": True,
        "traffic_targeting_mode": "random",
    }
    values.update(overrides)
    return JammerNode(**values)


def test_random_schedule_respects_configured_duty_cycle_budget() -> None:
    node = make_node(duty_cycle=0.02)

    transmissions = node.schedule_transmissions(sim_time_s=100.0, airtime_s=0.5, rng=random.Random(4))

    assert sum(event.duration_s for event in transmissions) <= 2.0
    assert len(transmissions) == 4
    assert transmissions == sorted(transmissions, key=lambda event: event.time_s)
    assert all(event.jammer_id == "jammer-1" for event in transmissions)
    assert all(event.sf == 7 for event in transmissions)
    assert all(event.frequency_mhz == 868.1 for event in transmissions)
    assert all(event.tx_power_dbm == 14.0 for event in transmissions)


def test_traffic_peak_schedule_clusters_transmissions_near_middle() -> None:
    node = make_node(traffic_targeting_mode="traffic_peak", synchronized=True)

    transmissions = node.schedule_transmissions(sim_time_s=100.0, airtime_s=0.25, rng=random.Random(2))

    assert len(transmissions) == 4
    assert [event.time_s for event in transmissions] == pytest.approx([40.0, 46.6666667, 53.3333333, 60.0])


def test_validate_duty_cycle_raises_above_one_percent() -> None:
    node = make_node()
    transmissions = [
        JammingEvent("jammer-1", 0.0, 0.7, 7, 868.1, 14.0),
        JammingEvent("jammer-1", 1.0, 0.4, 7, 868.1, 14.0),
    ]

    with pytest.raises(ValueError, match="Duty-cycle réglementaire dépassé"):
        node.validate_duty_cycle(sim_time_s=100.0, transmissions=transmissions)


def test_future_targeting_modes_are_explicitly_reserved() -> None:
    node = make_node(traffic_targeting_mode="reactive")

    with pytest.raises(NotImplementedError, match="pas encore fonctionnel"):
        node.schedule_transmissions(sim_time_s=100.0, airtime_s=1.0, rng=random.Random(1))

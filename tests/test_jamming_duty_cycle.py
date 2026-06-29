from __future__ import annotations

import random

from mobilesfrdth.jamming.jammer import MAX_REGULATORY_DUTY_CYCLE, JammerNode


def test_jammer_node_transmissions_never_exceed_one_percent_of_simulation_time() -> None:
    sim_time_s = 12.0
    airtime_s = 0.03
    node = JammerNode(
        jammer_id="jammer-1",
        spreading_factor=7,
        tx_power_dbm=14.0,
        frequency_mhz=868.1,
        bandwidth_khz=125.0,
        duty_cycle=MAX_REGULATORY_DUTY_CYCLE,
        position_x=0.0,
        position_y=0.0,
        synchronized=True,
        traffic_targeting_mode="random",
    )

    transmissions = node.schedule_transmissions(
        sim_time_s=sim_time_s, airtime_s=airtime_s, rng=random.Random(123)
    )

    total_airtime_s = sum(event.duration_s for event in transmissions)
    assert total_airtime_s <= MAX_REGULATORY_DUTY_CYCLE * sim_time_s
    node.validate_duty_cycle(sim_time_s=sim_time_s, transmissions=transmissions)

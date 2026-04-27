from __future__ import annotations

import random

from mobilesfrdth.scenarios import parse_grid_spec
from mobilesfrdth.simulator.engine import EventDrivenEngine, Node
from mobilesfrdth.simulator.mab.thompson import ThompsonSampling


def test_thompson_sampling_update_borne() -> None:
    agent = ThompsonSampling(n_arms=2, rng=random.Random(123))
    arm = agent.select_arm()
    agent.update(arm, reward=1.5)
    assert agent.alpha[arm] == 2.0
    assert agent.beta[arm] == 1.0


def test_parse_grid_supporte_thompson() -> None:
    grid = parse_grid_spec("N=10;mode=SNIR_ON;algo=THOMPSON;reps=1;seed_base=1")
    assert grid["algo"] == ["THOMPSON"]


def test_engine_run_supporte_algo_thompson() -> None:
    engine = EventDrivenEngine(seed=1)
    result = engine.run(
        nodes=[Node(node_id=1, period_s=10.0)],
        until_s=30.0,
        mode="snir_on",
        algo="thompson",
    )
    uplinks = [event for event in result.events if event.kind == "uplink"]
    assert uplinks

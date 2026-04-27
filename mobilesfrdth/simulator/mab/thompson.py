"""Thompson Sampling stationnaire (Beta-Bernoulli)."""

from __future__ import annotations

from dataclasses import dataclass, field
import random


@dataclass
class ThompsonSampling:
    n_arms: int
    rng: random.Random = field(default_factory=random.Random)
    alpha: list[float] = field(init=False)
    beta: list[float] = field(init=False)
    total_pulls: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.alpha = [1.0 for _ in range(self.n_arms)]
        self.beta = [1.0 for _ in range(self.n_arms)]

    def select_arm(self) -> int:
        samples = [self.rng.betavariate(self.alpha[arm], self.beta[arm]) for arm in range(self.n_arms)]
        return max(range(self.n_arms), key=lambda arm: samples[arm])

    def update(self, arm: int, reward: float) -> None:
        self.total_pulls += 1
        bounded_reward = min(max(float(reward), 0.0), 1.0)
        self.alpha[arm] += bounded_reward
        self.beta[arm] += 1.0 - bounded_reward

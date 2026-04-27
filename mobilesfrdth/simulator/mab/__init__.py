"""Algorithmes MAB."""

from .ucb import UCB1
from .ucb_forget import UCBForget
from .thompson import ThompsonSampling

__all__ = ["UCB1", "UCBForget", "ThompsonSampling"]

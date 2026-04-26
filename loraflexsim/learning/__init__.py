"""Composants d'apprentissage pour LoRaFlexSim."""

from .thompson import LoRaSFSelectorThompson
from .ucb1 import LoRaSFSelectorUCB1, UCB1Bandit

# Alias court pour la compatibilité avec les nouveaux scripts.
Thompson = LoRaSFSelectorThompson

__all__ = ["LoRaSFSelectorUCB1", "LoRaSFSelectorThompson", "Thompson", "UCB1Bandit"]

"""Sélecteur Thompson Sampling pour les facteurs d'étalement LoRa."""
from __future__ import annotations

import random
from typing import Dict, List


class LoRaSFSelectorThompson:
    """Sélecteur de facteur d'étalement basé sur Thompson Sampling.

    Les bras correspondent aux facteurs d'étalement ``SF7`` à ``SF12``.
    Chaque bras suit une loi bêta avec un a priori uniforme ``Beta(1, 1)``.
    """

    ARM_TO_SF: Dict[int, str] = {i: f"SF{7 + i}" for i in range(6)}
    SF_TO_ARM: Dict[str, int] = {sf: arm for arm, sf in ARM_TO_SF.items()}

    def __init__(self) -> None:
        self._n_arms = len(self.ARM_TO_SF)
        self.alpha: List[int] = [1 for _ in range(self._n_arms)]
        self.beta: List[int] = [1 for _ in range(self._n_arms)]

    def select_sf(self) -> str:
        """Retourne le facteur d'étalement sélectionné par Thompson Sampling."""

        thetas = [random.betavariate(self.alpha[arm], self.beta[arm]) for arm in range(self._n_arms)]
        selected_arm = int(max(range(self._n_arms), key=lambda arm: thetas[arm]))
        return self.ARM_TO_SF[selected_arm]

    def update(self, sf: str, *, success: bool) -> None:
        """Met à jour la postérieure du bras associé au facteur d'étalement choisi.

        choix volontaire d’un feedback binaire ACK/NACK pour comparabilité initiale avec UCB-SF.
        """

        arm = self.SF_TO_ARM[sf]
        if success:
            self.alpha[arm] += 1
        else:
            self.beta[arm] += 1

    def reset(self) -> None:
        """Réinitialise les a priori de tous les bras à ``Beta(1, 1)``."""

        self.alpha = [1 for _ in range(self._n_arms)]
        self.beta = [1 for _ in range(self._n_arms)]

"""Ordonnancement temporel des brouilleurs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JammerWindow:
    """Fenêtre d'activation d'un ou plusieurs brouilleurs."""

    start_s: float
    end_s: float
    jammer_ids: tuple[str, ...] = ()

    def contains(self, time_s: float) -> bool:
        return self.start_s <= time_s < self.end_s


class JammerScheduler:
    """Adaptateur stable pour interroger les fenêtres de brouillage."""

    def __init__(self, windows: list[JammerWindow] | None = None) -> None:
        self.windows = list(windows or [])

    def active_jammer_ids(self, time_s: float) -> set[str]:
        ids: set[str] = set()
        for window in self.windows:
            if window.contains(time_s):
                ids.update(window.jammer_ids)
        return ids

    def is_active(self, jammer_id: str, time_s: float) -> bool:
        return jammer_id in self.active_jammer_ids(time_s)


def periodic_windows(*, period_s: float, duration_s: float, active_s: float, jammer_ids: tuple[str, ...]) -> list[JammerWindow]:
    """Génère des fenêtres périodiques simples."""

    if period_s <= 0 or duration_s < 0 or active_s < 0:
        raise ValueError("period_s doit être > 0, duration_s et active_s doivent être >= 0.")
    windows: list[JammerWindow] = []
    t = 0.0
    while t < duration_s:
        windows.append(JammerWindow(start_s=t, end_s=min(t + active_s, duration_s), jammer_ids=jammer_ids))
        t += period_s
    return windows

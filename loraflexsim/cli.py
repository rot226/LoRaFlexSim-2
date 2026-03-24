"""Façade CLI publique alignée sur le package ``loraflexsim``."""

from __future__ import annotations

from mobilesfrdth.cli import main as _backend_main


def main() -> int:
    """Exécute la CLI publique ``loraflexsim`` via le backend interne actuel."""

    return _backend_main()

"""Entrée principale pour ``python -m loraflexsim`` et le script console ``loraflexsim``."""

from __future__ import annotations

from mobilesfrdth.cli import main as _legacy_main


def main() -> int:
    """Délègue à la CLI historique tant que la migration complète n'est pas finalisée."""

    return _legacy_main()


if __name__ == "__main__":
    raise SystemExit(main())

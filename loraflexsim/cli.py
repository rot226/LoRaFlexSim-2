"""Point d'entrée CLI public pour LoRaFlexSim."""

from __future__ import annotations

from collections.abc import Sequence

from mobilesfrdth.jamming.cli import main as _jamming_main


def main(argv: Sequence[str] | None = None) -> int:
    """Exécute la CLI jamming canonique."""

    return _jamming_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

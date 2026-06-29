"""Point d'entrée CLI de compatibilité pour LoRaFlexSim.

La CLI canonique des campagnes reste implémentée dans :mod:`mobilesfrdth.cli`.
Ce module fournit le nom de package public ``loraflexsim`` sans modifier le
comportement historique de ``python -m mobilesfrdth``.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from mobilesfrdth.cli import main as _mobilesfrdth_main


def _normalize_argv(argv: Sequence[str] | None) -> list[str] | None:
    """Retourne les arguments à transmettre à la CLI historique.

    ``loraflexsim campaign`` est conservé comme alias explicite de
    ``loraflexsim run`` pour les anciennes consignes de campagnes, tandis que
    les autres sous-commandes (dont ``run`` et ``aggregate``) sont transmises
    telles quelles.
    """

    if argv is None:
        args = sys.argv[1:]
    else:
        args = list(argv)

    if args and args[0] == "campaign":
        args[0] = "run"
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Exécute la CLI jamming/campagnes fournie par ``mobilesfrdth``."""

    return _mobilesfrdth_main(_normalize_argv(argv))


if __name__ == "__main__":
    raise SystemExit(main())

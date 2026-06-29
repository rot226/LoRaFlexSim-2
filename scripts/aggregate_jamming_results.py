"""Agrège des résultats de brouillage via la CLI canonique ``mobilesfrdth.jamming``.

Importer ce module ne déclenche aucun traitement; l'agrégation ne démarre que
par appel explicite à ``main`` ou par exécution directe du script.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mobilesfrdth.jamming.cli import main as jamming_cli_main  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    """Transmet les arguments à ``mobilesfrdth.jamming`` avec la commande aggregate."""

    args = list(argv) if argv is not None else sys.argv[1:]
    if not args or args[0] != "aggregate":
        args = ["aggregate", *args]
    return jamming_cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())

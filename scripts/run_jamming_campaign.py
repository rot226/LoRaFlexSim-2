"""Lance une campagne de brouillage via la CLI canonique ``mobilesfrdth.jamming``.

Ce module ne lance aucune simulation à l'import. L'exécution est protégée par
``if __name__ == "__main__"`` afin de rester sûr à importer depuis des tests ou
un notebook.
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
    """Transmet les arguments à ``mobilesfrdth.jamming`` avec la commande campaign."""

    args = list(argv) if argv is not None else sys.argv[1:]
    if not args or args[0] != "campaign":
        args = ["campaign", *args]
    return jamming_cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())

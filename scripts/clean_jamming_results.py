"""Nettoie les résultats de brouillage LoRaFlexSim avec confirmation explicite.

Par sécurité, l'import de ce module ne supprime rien. En exécution directe, la
suppression exige ``--yes`` ou une confirmation interactive.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mobilesfrdth.jamming.campaigns import CampaignLayout, is_run_complete  # noqa: E402

DEFAULT_RESULTS_DIR = ROOT_DIR / "results" / "jamming"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[DEFAULT_RESULTS_DIR],
        help="Fichier(s) ou dossier(s) de résultats jamming à supprimer (défaut: results/jamming).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirme explicitement la suppression sans invite interactive.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche ce qui serait supprimé sans toucher au disque.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Ignore les chemins absents au lieu de les signaler comme erreur.",
    )
    return parser


def _confirm(paths: Sequence[Path]) -> bool:
    print("Les chemins suivants seront supprimés:")
    for path in paths:
        print(f"  - {path}")
    answer = input("Confirmer la suppression? Taper 'yes' pour continuer: ")
    return answer.strip().lower() == "yes"


def _looks_like_complete_run(path: Path) -> bool:
    """Appelle une fonction jamming pour reconnaître un dossier de run complet."""

    if not path.is_dir():
        return False
    try:
        return is_run_complete(CampaignLayout(path))
    except (OSError, ValueError):
        return False


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    targets = [path.resolve() for path in args.paths]

    missing = [path for path in targets if not path.exists()]
    if missing and not args.allow_missing:
        for path in missing:
            print(f"Chemin absent: {path}", file=sys.stderr)
        return 2
    existing = [path for path in targets if path.exists()]

    complete_runs = [path for path in existing if _looks_like_complete_run(path)]
    if complete_runs:
        print("Runs jamming complets détectés:")
        for path in complete_runs:
            print(f"  - {path}")

    if args.dry_run:
        for path in existing:
            print(f"Dry-run: suppression prévue de {path}")
        return 0

    if not existing:
        print("Aucun résultat jamming à supprimer.")
        return 0

    if not args.yes:
        if not sys.stdin.isatty():
            print("Erreur: utilisez --yes pour confirmer en mode non interactif.", file=sys.stderr)
            return 2
        if not _confirm(existing):
            print("Suppression annulée.")
            return 1

    for path in existing:
        _remove(path)
        print(f"Supprimé: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

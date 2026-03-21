"""Chemins centralisés pour les sorties et artefacts pretest_campagne."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRETEST_ROOT = REPO_ROOT / "pretest_campagne"
RESULTS_ROOT = REPO_ROOT / "results" / "pretest_campagne"
FIGURES_ROOT = REPO_ROOT / "figures" / "pretest_campagne"

VALID_SCOPES = frozenset(
    {
        "common",
        "iwcmc_archive",
        "scenario_a",
        "scenario_b",
        "scenario_c",
        "scenario_d",
    }
)


def normalize_scope(scope: str) -> str:
    """Valide et normalise un identifiant de campagne courant."""

    cleaned = str(scope).strip()
    if not cleaned:
        raise ValueError("scope must not be empty")
    if cleaned not in VALID_SCOPES:
        valid = ", ".join(sorted(VALID_SCOPES))
        raise ValueError(f"scope must be one of: {valid}")
    return cleaned


def scenario_dir(scope: str, *parts: str | Path) -> Path:
    """Retourne un chemin dans l'arborescence source ``pretest_campagne/<scope>/...``."""

    return PRETEST_ROOT / normalize_scope(scope) / Path(*parts)


def results_dir(scope: str, *parts: str | Path) -> Path:
    """Retourne un chemin dans ``results/pretest_campagne/<scope>/...``."""

    return RESULTS_ROOT / normalize_scope(scope) / Path(*parts)


def results_file(scope: str, filename: str | Path) -> Path:
    """Retourne un fichier sous ``results/pretest_campagne/<scope>/``."""

    return results_dir(scope) / Path(filename)


def figures_dir(scope: str, *parts: str | Path) -> Path:
    """Retourne un chemin dans ``figures/pretest_campagne/<scope>/...``."""

    return FIGURES_ROOT / normalize_scope(scope) / Path(*parts)


def figures_file(scope: str, filename: str | Path, *parts: str | Path) -> Path:
    """Retourne un fichier sous ``figures/pretest_campagne/<scope>/...``."""

    return figures_dir(scope, *parts) / Path(filename)


def mne3sd_results_file(scope: str, filename: str | Path) -> Path:
    """Alias sémantique pour les CSV de scénarios MNE3SD migrés."""

    return results_file(scope, filename)


def mne3sd_figure_dir(scope: str, scenario: str, metric: str) -> Path:
    """Retourne le dossier de figures d'un scénario MNE3SD migré."""

    return figures_dir(scope, scenario, metric)


def archive_results_dir(*parts: str | Path) -> Path:
    """Retourne ``results/pretest_campagne/iwcmc_archive/...``."""

    return results_dir("iwcmc_archive", *parts)


def archive_figures_dir(*parts: str | Path) -> Path:
    """Retourne ``figures/pretest_campagne/iwcmc_archive/...``."""

    return figures_dir("iwcmc_archive", *parts)


def archive_source_dir(*parts: str | Path) -> Path:
    """Retourne ``pretest_campagne/iwcmc_archive/...`` pour les fichiers sources archivés."""

    return scenario_dir("iwcmc_archive", *parts)


def archive_snir_data_dir() -> Path:
    """Retourne le dossier des CSV SNIR statiques migrés."""

    return archive_results_dir("snir_static")


def archive_snir_data_file(figure_id: str, suffix: str = ".csv") -> Path:
    """Retourne le chemin du CSV SNIR statique pour une figure donnée."""

    normalized_suffix = suffix if str(suffix).startswith(".") else f".{suffix}"
    return archive_snir_data_dir() / f"{figure_id}{normalized_suffix}"


def archive_bundle_dir() -> Path:
    """Retourne le dossier des archives compressées pretest_campagne."""

    return archive_source_dir("archive")


def archive_bundle_filename(stamp: str) -> str:
    """Retourne le nom du tarball d'archive sans référence historique obsolète."""

    return f"pretest_campagne_archive_results_{stamp}.tar.gz"

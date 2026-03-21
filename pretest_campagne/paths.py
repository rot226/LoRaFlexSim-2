"""Chemins centralisés pour les sorties et artefacts pretest_campagne."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRETEST_ROOT = REPO_ROOT / "pretest_campagne"
RESULTS_ROOT = REPO_ROOT / "results" / "pretest_campagne"
FIGURES_ROOT = REPO_ROOT / "figures" / "pretest_campagne"

LEGACY_SCOPE_ALIASES = {
    "article_a": "scenario_a",
    "article_b": "scenario_b",
    "article_c": "scenario_c",
    "article_d": "scenario_d",
    "iwcmc": "iwcmc_archive",
}


def normalize_scope(scope: str) -> str:
    """Normalise un identifiant historique (``article_*``, ``iwcmc``) vers la cible pretest_campagne."""

    cleaned = str(scope).strip()
    if not cleaned:
        raise ValueError("scope must not be empty")
    return LEGACY_SCOPE_ALIASES.get(cleaned, cleaned)


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


def iwcmc_results_dir(*parts: str | Path) -> Path:
    """Retourne ``results/pretest_campagne/iwcmc_archive/...``."""

    return results_dir("iwcmc_archive", *parts)


def iwcmc_figures_dir(*parts: str | Path) -> Path:
    """Retourne ``figures/pretest_campagne/iwcmc_archive/...``."""

    return figures_dir("iwcmc_archive", *parts)


def iwcmc_source_dir(*parts: str | Path) -> Path:
    """Retourne ``pretest_campagne/iwcmc_archive/...`` pour les fichiers sources archivés."""

    return scenario_dir("iwcmc_archive", *parts)


def iwcmc_snir_data_dir() -> Path:
    """Retourne le dossier des CSV SNIR statiques migrés."""

    return iwcmc_results_dir("snir_static")


def iwcmc_snir_data_file(figure_id: str, suffix: str = ".csv") -> Path:
    """Retourne le chemin du CSV SNIR statique pour une figure donnée."""

    normalized_suffix = suffix if str(suffix).startswith(".") else f".{suffix}"
    return iwcmc_snir_data_dir() / f"{figure_id}{normalized_suffix}"


def iwcmc_archive_dir() -> Path:
    """Retourne le dossier des archives compressées pretest_campagne."""

    return iwcmc_source_dir("archive")


def iwcmc_archive_filename(stamp: str) -> str:
    """Retourne le nom du tarball d'archive sans référence historique à IWCMC."""

    return f"pretest_campagne_archive_results_{stamp}.tar.gz"

#!/usr/bin/env python3
"""Valide la préparation IEEE des résultats SNIR avec diagnostics actionnables."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ALGO_COLUMNS = ("algorithm", "algo")
SNIR_STATE_COLUMNS = ("snir_state", "snir", "snir_mode")
SNIR_FLAG_COLUMNS = ("with_snir", "use_snir", "snir_enabled")


@dataclass(frozen=True)
class Failure:
    title: str
    details: str
    suggestion: str


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _parse_snir_state(row: dict[str, str]) -> str | None:
    for column in SNIR_STATE_COLUMNS:
        raw = row.get(column)
        if raw is None:
            continue
        lowered = raw.strip().lower()
        if lowered in {"snir_on", "on", "true", "1", "yes", "y"}:
            return "snir_on"
        if lowered in {"snir_off", "off", "false", "0", "no", "n"}:
            return "snir_off"
    for column in SNIR_FLAG_COLUMNS:
        parsed = _parse_bool(row.get(column))
        if parsed is True:
            return "snir_on"
        if parsed is False:
            return "snir_off"
    return None


def _get_algo(row: dict[str, str]) -> str:
    for column in ALGO_COLUMNS:
        value = (row.get(column) or "").strip()
        if value:
            return value
    return "<algo_inconnu>"


def _read_csv_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                row["__source"] = str(path)
                rows.append(row)
    return rows


def _discover_csv_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in inputs:
        if path.is_file() and path.suffix.lower() == ".csv":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.csv")))
    return files


def _check_principal_axes(
    rows: list[dict[str, str]],
    principal_axes: list[str],
    min_levels: int,
    failures: list[Failure],
) -> None:
    for axis in principal_axes:
        values = sorted({float(v) for row in rows if (v := _to_float(row.get(axis))) is not None})
        if len(values) < min_levels:
            rendered = ", ".join(f"{v:.6g}" for v in values) if values else "aucune"
            failures.append(
                Failure(
                    title=f"Axe principal insuffisant: {axis}",
                    details=(
                        f"{len(values)} niveau(x) distinct(s) détecté(s) pour '{axis}' "
                        f"(minimum requis: {min_levels}). Niveaux observés: {rendered}."
                    ),
                    suggestion=(
                        f"Ajouter des campagnes couvrant au moins {min_levels} valeurs de '{axis}' "
                        "(ex: faible, moyen, élevé)."
                    ),
                )
            )


def _check_identical_curves(
    rows: list[dict[str, str]],
    metrics: list[str],
    principal_axes: list[str],
    tolerance: float,
    failures: list[Failure],
) -> None:
    for metric in metrics:
        signatures: dict[tuple[str, str], tuple[tuple[tuple[float, ...], float], ...]] = {}
        by_series: dict[tuple[str, str], dict[tuple[float, ...], list[float]]] = defaultdict(lambda: defaultdict(list))
        for row in rows:
            value = _to_float(row.get(metric))
            if value is None:
                continue
            coords: list[float] = []
            missing_axis = False
            for axis in principal_axes:
                parsed = _to_float(row.get(axis))
                if parsed is None:
                    missing_axis = True
                    break
                coords.append(parsed)
            if missing_axis:
                continue
            by_series[(_get_algo(row), _parse_snir_state(row) or "snir_unknown")][tuple(coords)].append(value)

        for series_key, points in by_series.items():
            ordered = []
            for coord in sorted(points):
                avg = sum(points[coord]) / len(points[coord])
                rounded = round(avg / tolerance) * tolerance
                ordered.append((coord, rounded))
            signatures[series_key] = tuple(ordered)

        keys = sorted(signatures)
        for idx, left in enumerate(keys):
            left_sig = signatures[left]
            if len(left_sig) < 2:
                continue
            for right in keys[idx + 1 :]:
                right_sig = signatures[right]
                if left_sig == right_sig and len(right_sig) >= 2:
                    failures.append(
                        Failure(
                            title=f"Courbes identiques détectées ({metric})",
                            details=(
                                f"Les séries {left[0]}[{left[1]}] et {right[0]}[{right[1]}] "
                                "sont strictement identiques sur les axes principaux."
                            ),
                            suggestion=(
                                "Vérifier la génération des métriques (seed, paramètres, mapping des algorithmes) "
                                "et relancer la simulation pour éviter un duplicat de courbe."
                            ),
                        )
                    )


def _check_non_zero_variance(
    rows: list[dict[str, str]],
    metrics: list[str],
    tolerance: float,
    failures: list[Failure],
) -> None:
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        algo = _get_algo(row)
        state = _parse_snir_state(row) or "snir_unknown"
        for metric in metrics:
            parsed = _to_float(row.get(metric))
            if parsed is not None:
                grouped[(algo, state, metric)].append(parsed)

    for (algo, state, metric), values in sorted(grouped.items()):
        if len(values) < 2:
            continue
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        if variance <= tolerance:
            failures.append(
                Failure(
                    title=f"Variance nulle ({metric})",
                    details=(
                        f"Variance={variance:.3e} pour {algo}[{state}] sur {len(values)} point(s)."
                    ),
                    suggestion=(
                        "Augmenter la diversité des conditions (charge, nœuds, intervalle, seed) "
                        "et vérifier que la colonne n'est pas figée par un post-traitement."
                    ),
                )
            )


def _check_snir_coherence(
    rows: list[dict[str, str]],
    metrics: list[str],
    principal_axes: list[str],
    tolerance: float,
    failures: list[Failure],
) -> None:
    grouped: dict[tuple[str, tuple[float, ...]], dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: {"snir_on": [], "snir_off": []}
    )
    for row in rows:
        state = _parse_snir_state(row)
        if state not in {"snir_on", "snir_off"}:
            continue
        coords: list[float] = []
        for axis in principal_axes:
            parsed = _to_float(row.get(axis))
            if parsed is None:
                coords = []
                break
            coords.append(parsed)
        if not coords:
            continue
        grouped[(_get_algo(row), tuple(coords))][state].append(row)

    if not grouped:
        failures.append(
            Failure(
                title="Comparaison SNIR_ON/SNIR_OFF impossible",
                details="Aucun groupe comparable (algo + axes principaux) n'a été trouvé.",
                suggestion="Exporter les colonnes SNIR (snir_state/with_snir) et les axes principaux dans les CSV.",
            )
        )
        return

    for metric in metrics:
        deltas: list[float] = []
        incomplete = 0
        for _, bundle in grouped.items():
            if not bundle["snir_on"] or not bundle["snir_off"]:
                incomplete += 1
                continue
            on_values = [_to_float(row.get(metric)) for row in bundle["snir_on"]]
            off_values = [_to_float(row.get(metric)) for row in bundle["snir_off"]]
            on_clean = [v for v in on_values if v is not None]
            off_clean = [v for v in off_values if v is not None]
            if not on_clean or not off_clean:
                continue
            deltas.append((sum(on_clean) / len(on_clean)) - (sum(off_clean) / len(off_clean)))

        if incomplete > 0:
            failures.append(
                Failure(
                    title=f"Paires SNIR incomplètes ({metric})",
                    details=(
                        f"{incomplete} groupe(s) ne contiennent pas les deux états SNIR_ON et SNIR_OFF."
                    ),
                    suggestion="Régénérer les campagnes manquantes pour chaque algo et chaque point de grille.",
                )
            )

        significant = [delta for delta in deltas if abs(delta) > tolerance]
        if not deltas or not significant:
            failures.append(
                Failure(
                    title=f"Effet SNIR non observable ({metric})",
                    details="Les écarts ON-OFF sont nuls ou sous la tolérance sur tous les groupes comparables.",
                    suggestion="Vérifier que SNIR_ON et SNIR_OFF activent réellement des modèles différents.",
                )
            )
            continue

        has_pos = any(delta > tolerance for delta in significant)
        has_neg = any(delta < -tolerance for delta in significant)
        if has_pos and has_neg:
            failures.append(
                Failure(
                    title=f"Cohérence SNIR instable ({metric})",
                    details=(
                        "Le signe de l'écart ON-OFF change selon les groupes "
                        "(amélioration et dégradation mélangées)."
                    ),
                    suggestion=(
                        "Vérifier la définition du scénario de référence et harmoniser les paramètres "
                        "pour éviter les inversions ON/OFF involontaires."
                    ),
                )
            )


def validate(args: argparse.Namespace) -> list[Failure]:
    csv_files = _discover_csv_files(args.inputs)
    if not csv_files:
        return [
            Failure(
                title="Aucun CSV détecté",
                details="Aucun fichier .csv trouvé dans les chemins fournis.",
                suggestion="Passer un fichier CSV ou un répertoire contenant les exports IEEE.",
            )
        ]

    rows = _read_csv_rows(csv_files)
    if not rows:
        return [
            Failure(
                title="CSV vides",
                details="Les fichiers trouvés ne contiennent aucune ligne exploitable.",
                suggestion="Vérifier l'export des simulations et la présence d'en-têtes valides.",
            )
        ]

    failures: list[Failure] = []
    _check_principal_axes(rows, args.principal_axes, args.min_levels, failures)
    _check_identical_curves(rows, args.key_metrics, args.principal_axes, args.tolerance, failures)
    _check_non_zero_variance(rows, args.important_metrics, args.tolerance, failures)
    _check_snir_coherence(rows, args.key_metrics, args.principal_axes, args.tolerance, failures)
    return failures


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        type=Path,
        nargs="+",
        help="Fichier(s) CSV ou répertoire(s) contenant les CSV à valider.",
    )
    parser.add_argument(
        "--principal-axes",
        nargs="+",
        default=["num_nodes", "packet_interval_s"],
        help="Axes principaux qui doivent avoir au moins 3 niveaux distincts.",
    )
    parser.add_argument(
        "--key-metrics",
        nargs="+",
        default=["pdr", "der", "throughput_bps"],
        help="Métriques clés pour la détection de courbes identiques et la cohérence SNIR.",
    )
    parser.add_argument(
        "--important-metrics",
        nargs="+",
        default=["pdr", "der", "throughput_bps", "snir_mean", "snir_median"],
        help="Métriques dont la variance doit être strictement positive.",
    )
    parser.add_argument(
        "--min-levels",
        type=int,
        default=3,
        help="Nombre minimum de niveaux distincts requis par axe principal.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-9,
        help="Tolérance numérique pour les comparaisons d'égalité.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    failures = validate(args)
    if failures:
        print("❌ Validation IEEE échouée.")
        print(f"   {len(failures)} problème(s) détecté(s):")
        for idx, failure in enumerate(failures, start=1):
            print(f"\n[{idx}] {failure.title}")
            print(f"    Diagnostic : {failure.details}")
            print(f"    Suggestion : {failure.suggestion}")
        return 1

    print("✅ Validation IEEE réussie : dataset prêt pour revue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

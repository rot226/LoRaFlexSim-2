"""Interface CLI pour mobilesfrdth."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from time import monotonic

from .scenarios import generate_jobs, parse_grid_spec


MIN_SUPPORTED_PYTHON = (3, 11)
MAX_SUPPORTED_PYTHON_EXCLUSIVE = (3, 15)

PROFILE_PRESETS: dict[str, str] = {
    "smoke": "N=40,100,200;speed=1;mode=SNIR_OFF,SNIR_ON;algo=ADR,UCB;reps=1;duration_s=300;seed_base=1234",
    "paper_core": "N=40,60,80,100,120,140,160,180,200;speed=1,3;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET;reps=8;duration_s=3600;seed_base=1234",
    "paper_extended": "N=40,60,80,100,120,140,160,180,200;speed=0,1,3,5;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET;reps=10;duration_s=5400;seed_base=1234",
    # Alias rétro-compatibilité (anciens profils documentés).
    "core": "N=50,100,160;speed=1,3;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET;reps=2;duration_s=1800;seed_base=1234",
    "full": "N=50,100,160,320;speed=0,1,3,6;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET;reps=5;duration_s=3600;seed_base=1234",
}


def _existing_file(value: str) -> Path:
    path = Path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Fichier introuvable: {path}")
    return path


def _existing_path(value: str) -> Path:
    path = Path(value)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"Chemin introuvable: {path}")
    return path


def _sf_range(value: str) -> tuple[int, int]:
    token = value.strip()
    sep = "-" if "-" in token else ":" if ":" in token else None
    if sep is None:
        raise argparse.ArgumentTypeError("Format attendu pour --sf-range: min-max (ex: 7-12).")
    left, right = [part.strip() for part in token.split(sep, 1)]
    if not left or not right:
        raise argparse.ArgumentTypeError("--sf-range incomplet, utiliser min-max.")
    try:
        return int(left), int(right)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--sf-range doit contenir des entiers.") from exc


def _positive_int(value: str, *, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} doit être un entier.") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError(f"{name} doit être >= 1.")
    return parsed


def _seed_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--seed doit être un entier.") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("--seed doit être >= 0.")
    return parsed


def _positive_float(value: str, *, name: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} doit être un nombre.") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"{name} doit être > 0.")
    return parsed


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _format_eta(seconds: float | None) -> str:
    if seconds is None:
        return "N/A"
    total = max(int(seconds), 0)
    hours, rem = divmod(total, 3600)
    minutes, sec = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"


def _campaign_log_path(out_dir: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    return out_dir.parent / "campaign_log.jsonl"


def _append_campaign_log(path: Path, *, step: str, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"step": step, **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _error_categories(failures: list[dict[str, object]]) -> dict[str, int]:
    categories: dict[str, int] = {}
    for failure in failures:
        raw_error = failure.get("error")
        category = "UnknownError"
        if isinstance(raw_error, str) and raw_error:
            try:
                payload = json.loads(raw_error)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                parsed = payload.get("error_type")
                if isinstance(parsed, str) and parsed.strip():
                    category = parsed.strip()
        categories[category] = categories.get(category, 0) + 1
    return categories


def cmd_run(args: argparse.Namespace) -> int:
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if args.grid:
            grid_spec = args.grid
        elif args.profile:
            grid_spec = PROFILE_PRESETS[args.profile]
            print(f"Profil sélectionné: {args.profile}")
        else:
            raise SystemExit("Erreur: fournir --grid ou --profile.")

        grid = parse_grid_spec(grid_spec)
        jobs = generate_jobs(
            config_path=args.config,
            output_root=out_dir,
            grid=grid,
            seed=args.seed,
            reps=args.reps,
            sf_range=args.sf_range,
        )
    except ValueError as exc:
        raise SystemExit(f"Erreur de validation: {exc}") from exc

    payload = {
        "config": str(args.config),
        "grid": grid,
        "seed": args.seed,
        "reps": args.reps,
        "sf_range": list(args.sf_range) if args.sf_range else None,
        "jobs": jobs,
        "num_jobs": len(jobs),
    }
    output_file = out_dir / "jobs.json"
    _dump_json(output_file, payload)

    from .simulator.engine import GridRunOrchestrator

    orchestrator = GridRunOrchestrator(output_root=out_dir)
    start_s = monotonic()

    def _on_run_complete(run_report, run_i, total, success_count, failure_count, eta_s):
        status = "succès" if run_report.success else "échec"
        print(
            f"[{run_i}/{total}] {run_report.run_id}: {status} | "
            f"ETA={_format_eta(eta_s)} | succès={success_count} échec={failure_count}"
        )

    campaign_log_file = _campaign_log_path(out_dir, args.campaign_log)
    print(f"Run: progression des runs ({len(jobs)} au total).")

    report = orchestrator.execute_jobs(
        jobs,
        fail_fast=args.fail_fast,
        resume=args.resume,
        max_runs=args.max_runs,
        max_walltime_s=args.max_walltime,
        progress_interval_s=args.progress_interval,
        verbose=args.verbose,
        on_run_complete=_on_run_complete,
    )
    failures = [
        {"run_id": item.run_id, "error": item.error, "run_dir": str(item.run_dir)}
        for item in report.failed_reports
    ]
    executed_runs = len(report.reports)
    successful_runs = executed_runs - len(failures)
    execution_summary = {
        "num_jobs": report.total_jobs,
        "num_scheduled": report.scheduled_runs,
        "num_executed": executed_runs,
        "num_skipped": report.skipped_runs,
        "num_success": successful_runs,
        "num_failures": len(failures),
        "error_categories": _error_categories(failures),
        "interrupted": report.interrupted,
        "elapsed_s": monotonic() - start_s,
        "failures": failures,
    }
    summary_file = out_dir / "batch_summary.json"
    _dump_json(summary_file, execution_summary)

    print(f"{len(jobs)} jobs générés dans {output_file}")
    print(
        "Exécution terminée: "
        f"{execution_summary['num_success']} succès, "
        f"{execution_summary['num_failures']} échec(s), "
        f"{execution_summary['num_skipped']} ignoré(s)."
    )
    if execution_summary["interrupted"]:
        print("Exécution interrompue (Ctrl+C): bilan partiel écrit.")
    print(f"Résumé batch écrit dans {summary_file}")
    _append_campaign_log(
        campaign_log_file,
        step="run",
        payload={
            "out_dir": str(out_dir),
            "jobs_file": str(output_file),
            "summary_file": str(summary_file),
            "num_jobs": len(jobs),
            "num_success": successful_runs,
            "num_failures": len(failures),
            "num_skipped": report.skipped_runs,
            "interrupted": report.interrupted,
        },
    )
    print(f"Log campagne mis à jour: {campaign_log_file}")
    return 130 if execution_summary["interrupted"] else (1 if failures else 0)


def cmd_aggregate(args: argparse.Namespace) -> int:
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from .simulator.io import aggregate_runs, summarize_run_completeness

        completeness = summarize_run_completeness(args.results)
        expected_runs = completeness["expected_runs"]
        found_runs = int(completeness["found_runs"])
        missing_runs = int(completeness["missing_runs"])
        if args.strict_completeness and expected_runs is not None and found_runs != expected_runs:
            print(
                "Erreur de complétude: "
                f"{found_runs} run(s) trouvé(s) pour {expected_runs} attendu(s) "
                f"(manquants={missing_runs})."
            )
            return 2

        ignored_runs: list[dict[str, str]] = []
        files = aggregate_runs(
            inputs=args.results,
            output_root=out_dir,
            summary_only=args.summary_only,
            skip_sinr_cdf=args.skip_sinr_cdf,
            skip_sf_distribution=args.skip_sf_distribution,
            strict=args.strict,
            verbose=args.verbose,
            ignored_runs_report=ignored_runs,
        )
    except (ValueError, json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"Erreur pendant l'agrégation: {exc}")
        return 2

    manifest = {
        "num_inputs": len(args.results),
        "sources": [str(path) for path in args.results],
        "expected_runs": expected_runs,
        "found_runs": found_runs,
        "missing_runs": missing_runs,
        "n_runs_effective": max(found_runs - len(ignored_runs), 0),
        "ignored_runs": ignored_runs,
        "files": {name: str(path) for name, path in files.items()},
    }

    metric_by_factor_path = files.get("metric_by_factor")
    distinct_groups_by_algo: dict[str, int] = {}
    if metric_by_factor_path is not None:
        with metric_by_factor_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                algo = str(row.get("algo", ""))
                distinct_groups_by_algo[algo] = distinct_groups_by_algo.get(algo, 0) + 1

    manifest["distinct_groups_by_algo"] = distinct_groups_by_algo
    output_file = out_dir / "aggregate.json"
    _dump_json(output_file, manifest)

    total_groups = sum(distinct_groups_by_algo.values())
    print(
        "Aggregate: "
        f"groupes détectés={total_groups}, scénarios/run détectés={found_runs}, manquants={missing_runs}"
    )
    print(f"Agrégation écrite dans {output_file}")

    campaign_log_file = _campaign_log_path(out_dir, args.campaign_log)
    _append_campaign_log(
        campaign_log_file,
        step="aggregate",
        payload={
            "out_dir": str(out_dir),
            "aggregate_file": str(output_file),
            "num_inputs": len(args.results),
            "found_runs": found_runs,
            "missing_runs": missing_runs,
            "groups_by_algo": distinct_groups_by_algo,
            "total_groups": total_groups,
        },
    )
    print(f"Log campagne mis à jour: {campaign_log_file}")
    return 0


def cmd_plots(args: argparse.Namespace) -> int:
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    aggregates_dir = args.aggregates_dir or args.aggregates
    if aggregates_dir is None:
        print("Erreur: fournir --aggregates-dir (ou alias --aggregates).")
        return 2
    if (aggregates_dir / "aggregates").is_dir():
        aggregates_dir = aggregates_dir / "aggregates"

    from .plotting.plots import ScenarioFilters, generate_minimal_figures, validate_aggregates_inputs

    errors = validate_aggregates_inputs(aggregates_dir)
    if errors:
        print("Prérequis manquants pour plotting:")
        for err in errors:
            print(f"- {err}")
        return 2

    generated, traces = generate_minimal_figures(
        aggregates_dir=aggregates_dir,
        out_dir=out_dir,
        filters=ScenarioFilters.from_tokens(args.scenario_filter),
        article_profile=args.article_profile,
        include_bonus=not args.no_bonus,
        verbose=args.verbose,
        ieee_ready=args.ieee_ready,
        y_scale=args.y_scale,
    )
    report = {
        "article_profile": args.article_profile,
        "aggregates_dir": str(aggregates_dir),
        "out_dir": str(out_dir),
        "num_figures": len(generated),
        "figures": [str(path) for path in generated],
        "figure_filters": [
            {
                "figure": trace.figure,
                "source": trace.source,
                "metric": trace.metric,
                "filters": trace.filters,
                "num_points": trace.num_points,
                "points_by_curve": trace.points_by_curve,
                "generated": trace.generated,
            }
            for trace in traces
        ],
    }
    output_file = out_dir / "plots_summary.json"
    _dump_json(output_file, report)
    print(f"Plots: dataset utilisé={aggregates_dir}")
    for trace in traces:
        print(
            f"- {trace.figure} | source={trace.source} | filtres={trace.filters} "
            f"| points={trace.num_points} | points/courbe={trace.points_by_curve}"
        )
    print(f"{len(generated)} figure(s) écrite(s) dans {out_dir}")
    print(f"Résumé de plots écrit dans {output_file}")

    if args.strict:
        from .qa.validate_results import validate_strict_plot_outputs

        issues = validate_strict_plot_outputs(
            aggregates_dir=aggregates_dir,
            figure_filters=report["figure_filters"],
        )
        if issues:
            print("Validation stricte échouée:")
            for issue in issues:
                print(f"- {issue}")
            return 2

    campaign_log_file = _campaign_log_path(out_dir, args.campaign_log)
    _append_campaign_log(
        campaign_log_file,
        step="plots",
        payload={
            "aggregates_dir": str(aggregates_dir),
            "out_dir": str(out_dir),
            "plots_summary": str(output_file),
            "num_figures": len(generated),
            "figures": [
                {
                    "figure": trace.figure,
                    "source": trace.source,
                    "filters": trace.filters,
                    "num_points": trace.num_points,
                    "points_by_curve": trace.points_by_curve,
                    "generated": trace.generated,
                }
                for trace in traces
            ],
        },
    )
    print(f"Log campagne mis à jour: {campaign_log_file}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mobilesfrdth",
        description="CLI de campagnes mobile-sfrd_th: génération, agrégation et préparation des plots.",
        epilog=(
            "Exemple grille: N=40,60,80,100,120,140,160,180,200;speed=1,3;reps=8;seed_base=1234\n"
            "Exemple run: mobilesfrdth run --config experiments/default.yaml --out runs --profile paper_core"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Génère les jobs puis exécute la campagne.")
    run_parser.add_argument("--config", required=True, type=_existing_file, help="Fichier de configuration de base.")
    run_parser.add_argument("--out", required=True, type=Path, help="Répertoire de sortie (jobs.json, results/<run_id>/...).")
    run_parser.add_argument(
        "--grid",
        required=False,
        help=(
            "Grille de sweep au format clé=v1,v2;clé2=v3,v4 (ex: N=50,100;speed=1,3). "
            "Pour time_bin_s: recommandé 10s pour comparabilité Tc, mais autres valeurs > 0 autorisées."
        ),
    )
    run_parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_PRESETS),
        help="Profil prédéfini de campagne (smoke, paper_core, paper_extended). Utilisable à la place de --grid.",
    )
    run_parser.add_argument(
        "--seed",
        type=_seed_int,
        default=None,
        help="Seed globale (entier >= 0) injectée dans chaque job si absente de --grid.",
    )
    run_parser.add_argument(
        "--reps",
        type=lambda value: _positive_int(value, name="--reps"),
        default=None,
        help="Nombre de répétitions par job (entier >= 1).",
    )
    run_parser.add_argument(
        "--sf-range",
        type=_sf_range,
        default=None,
        help="Plage SF globale, format min-max (bornes attendues: 7-12).",
    )
    run_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Arrête la campagne au premier run en échec (par défaut, continue les runs restants).",
    )
    run_parser.add_argument(
        "--resume",
        action="store_true",
        help="Reprend une campagne existante en sautant les runs déjà complets dans --out/results.",
    )
    run_parser.add_argument(
        "--max-runs",
        type=lambda value: _positive_int(value, name="--max-runs"),
        default=None,
        help="Limite le nombre de runs exécutés pendant cet appel (utile pour reprendre par tranches).",
    )
    run_parser.add_argument(
        "--progress-interval",
        type=lambda value: _positive_float(value, name="--progress-interval"),
        default=30.0,
        help="Intervalle (secondes) entre deux logs de progression par run.",
    )
    run_parser.add_argument(
        "--max-walltime",
        type=lambda value: _positive_float(value, name="--max-walltime"),
        default=None,
        help="Durée murale max en secondes pour la commande run (arrêt propre au-delà).",
    )
    run_parser.add_argument("--verbose", action="store_true", help="Affiche des détails de progression supplémentaires.")
    run_parser.add_argument(
        "--campaign-log",
        type=Path,
        default=None,
        help="Chemin du log campagne JSONL (par défaut: ../campaign_log.jsonl depuis --out).",
    )
    run_parser.set_defaults(func=cmd_run)

    aggregate_parser = subparsers.add_parser(
        "aggregate", help="Agrège plusieurs runs et produit les CSV standards dans aggregates/."
    )
    aggregate_parser.add_argument(
        "--results",
        required=True,
        nargs="+",
        type=_existing_path,
        help="Un ou plusieurs chemins vers des runs (ou un dossier contenant results/<run_id>/...).",
    )
    aggregate_parser.add_argument("--out", required=True, type=Path, help="Répertoire où écrire aggregates/*.csv et aggregate.json.")
    aggregate_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Agrège uniquement les summary.csv (rapide, n'ouvre pas events.csv).",
    )
    aggregate_parser.add_argument(
        "--skip-sinr-cdf",
        action="store_true",
        help="N'écrit pas sinr_cdf.csv pour accélérer l'agrégation.",
    )
    aggregate_parser.add_argument(
        "--skip-sf-distribution",
        action="store_true",
        help="N'écrit pas distribution_sf.csv pour accélérer l'agrégation.",
    )
    aggregate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Échoue si un run incomplet est détecté au lieu de l'ignorer.",
    )
    aggregate_parser.add_argument(
        "--strict-completeness",
        action="store_true",
        help="Échoue si num_jobs (jobs.json) ne correspond pas au nombre de run dirs trouvés.",
    )
    aggregate_parser.add_argument("--verbose", action="store_true", help="Affiche le détail des dossiers traités.")
    aggregate_parser.add_argument(
        "--campaign-log",
        type=Path,
        default=None,
        help="Chemin du log campagne JSONL (par défaut: ../campaign_log.jsonl depuis --out).",
    )
    aggregate_parser.set_defaults(func=cmd_aggregate)

    plots_parser = subparsers.add_parser(
        "plots", help="Génère les figures fig01..fig10 (et bonus fig11..fig16) depuis aggregates/*.csv."
    )
    plots_parser.add_argument(
        "--aggregates-dir",
        type=_existing_path,
        help="Répertoire contenant les CSV d'agrégats (metric_by_factor.csv, sinr_cdf.csv, ...).",
    )
    plots_parser.add_argument(
        "--aggregates",
        type=_existing_path,
        help="Alias de --aggregates-dir pour compatibilité des commandes existantes.",
    )
    plots_parser.add_argument("--out", required=True, type=Path, help="Répertoire où écrire les figures PNG.")
    plots_parser.add_argument(
        "--scenario-filter",
        action="append",
        default=[],
        help="Filtre clé=val1,val2 (répétable), ex: --scenario-filter algo=ucb --scenario-filter mobility_model=rwp.",
    )
    plots_parser.add_argument(
        "--article-profile",
        choices=["core", "full"],
        default="core",
        help="Profil de filtres documentés à appliquer pour chaque figure (core ou full).",
    )
    plots_parser.add_argument("--no-bonus", action="store_true", help="Désactive les figures bonus fig11..fig16.")
    plots_parser.add_argument("--verbose", action="store_true", help="Affiche le statut de chaque figure générée/ignorée.")
    plots_parser.add_argument(
        "--ieee-ready",
        action="store_true",
        help="Active automatiquement le style IEEE-ready (polices/taille/couleurs), dpi=300 et export PDF+PNG.",
    )
    plots_parser.add_argument(
        "--y-scale",
        choices=["auto", "full", "zoom"],
        default="auto",
        help="Politique d'échelle Y pour PDR/DER: auto (zoom si proche de 1 + annexe full), full ([0,1]), zoom.",
    )
    plots_parser.add_argument(
        "--campaign-log",
        type=Path,
        default=None,
        help="Chemin du log campagne JSONL (par défaut: ../campaign_log.jsonl depuis --out).",
    )
    plots_parser.add_argument(
        "--strict",
        action="store_true",
        help="Active la validation QA stricte des agrégats et figures (échec si résultats suspects).",
    )
    plots_parser.set_defaults(func=cmd_plots)

    return parser


def _ensure_supported_python() -> bool:
    major, minor = sys.version_info[:2]
    return MIN_SUPPORTED_PYTHON <= (major, minor) < MAX_SUPPORTED_PYTHON_EXCLUSIVE


def main(argv: list[str] | None = None) -> int:
    if not _ensure_supported_python():
        print(
            "Version Python non supportée: utiliser une version >=3.11 et <3.15.",
            file=sys.stderr,
        )
        return 2

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except ValueError as exc:
        print(f"Erreur: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

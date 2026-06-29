"""Interface CLI pour mobilesfrdth."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import sys
from collections import Counter
from pathlib import Path
from time import monotonic

from .presets import inject_preset_args, list_presets
from .scenarios import generate_jobs, parse_grid_spec


MIN_SUPPORTED_PYTHON = (3, 11)
MAX_SUPPORTED_PYTHON_EXCLUSIVE = (3, 13)

PROFILE_PRESETS: dict[str, str] = {
    "smoke": "N=40,100,200;speed=1;mode=SNIR_OFF,SNIR_ON;algo=ADR,UCB;reps=1;duration_s=300;seed_base=1234",
    "paper_core": "N=40,60,80,100,120,140,160,180,200;speed=1,3;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET,THOMPSON;reps=8;duration_s=3600;seed_base=1234",
    "paper_extended": "N=40,60,80,100,120,140,160,180,200;speed=0,1,3,5;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET,THOMPSON;reps=10;duration_s=5400;seed_base=1234",
    # Alias rétro-compatibilité (anciens profils documentés).
    "core": "N=50,100,160;speed=1,3;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET,THOMPSON;reps=2;duration_s=1800;seed_base=1234",
    "full": "N=50,100,160,320;speed=0,1,3,6;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET,THOMPSON;reps=5;duration_s=3600;seed_base=1234",
}

PLOTS_NO_FIGURES_EXIT_CODE = 3
PLOTS_NO_FIGURES_README_LINK = "README.md#no-figures-generated"
PLOTS_PROFILE_CHOICES = ["exploratory", "publication"]



def _dominant_context_from_plots_diagnostics(diagnostics_file: Path) -> dict[str, str]:
    if not diagnostics_file.is_file():
        return {}
    try:
        payload = json.loads(diagnostics_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    figures = payload.get("figures")
    if not isinstance(figures, list):
        return {}

    counts: Counter[tuple[tuple[str, str], ...]] = Counter()
    dimensions = ("mode", "speed", "mobility_model", "gateways", "sigma_shadowing")
    for item in figures:
        if not isinstance(item, dict):
            continue
        grouping = item.get("grouping")
        if not isinstance(grouping, dict):
            continue
        selected = grouping.get("selected_context")
        if not isinstance(selected, dict):
            continue
        normalized = {
            dim: str(selected.get(dim, "")).strip()
            for dim in dimensions
            if str(selected.get(dim, "")).strip()
        }
        if not normalized:
            continue
        key = tuple(sorted(normalized.items()))
        counts[key] += 1

    if not counts:
        return {}

    dominant, _ = counts.most_common(1)[0]
    return dict(dominant)


def _scenario_filter_resume_tokens(base_filters: list[str], dominant_context: dict[str, str]) -> list[str]:
    merged: dict[str, list[str]] = {}
    for token in base_filters:
        if "=" not in token:
            continue
        key, raw_values = token.split("=", 1)
        key = key.strip()
        values = [value.strip() for value in raw_values.split(",") if value.strip()]
        if key and values:
            merged[key] = values

    if "mode" in dominant_context:
        merged["mode"] = [dominant_context["mode"]]
    if "speed" in dominant_context:
        merged["speed"] = [dominant_context["speed"]]
    if "mobility_model" in dominant_context:
        merged["model"] = [dominant_context["mobility_model"]]
    if "gateways" in dominant_context:
        merged["gateways"] = [dominant_context["gateways"]]
    if "sigma_shadowing" in dominant_context:
        merged["sigma"] = [dominant_context["sigma_shadowing"]]

    ordered_keys = ["mode", "speed", "model", "gateways", "sigma"]
    for key in sorted(merged):
        if key not in ordered_keys:
            ordered_keys.append(key)

    tokens: list[str] = []
    for key in ordered_keys:
        values = merged.get(key)
        if values:
            tokens.append(f"{key}={','.join(values)}")
    return tokens


def _build_plots_resume_command(*, aggregates_dir: Path, out_dir: Path, profile: str, article_profile: str, no_bonus: bool, ieee_ready: bool, y_scale: str, strict: bool, scenario_filter_tokens: list[str]) -> str:
    cmd_parts = [
        "mobilesfrdth",
        "plots",
        "--aggregates-dir",
        str(aggregates_dir),
        "--out",
        str(out_dir),
        "--profile",
        profile,
        "--article-profile",
        article_profile,
        "--y-scale",
        y_scale,
    ]
    if no_bonus:
        cmd_parts.append("--no-bonus")
    if ieee_ready:
        cmd_parts.append("--ieee-ready")
    if strict:
        cmd_parts.append("--strict")
    for token in scenario_filter_tokens:
        cmd_parts.extend(["--scenario-filter", token])
    return " ".join(shlex.quote(part) for part in cmd_parts)


def _build_plots_resume_command_powershell(*, aggregates_dir: Path, out_dir: Path, profile: str, article_profile: str, no_bonus: bool, ieee_ready: bool, y_scale: str, strict: bool, scenario_filter_tokens: list[str]) -> str:
    cmd_parts = [
        "mobilesfrdth",
        "plots",
        "--aggregates-dir",
        str(aggregates_dir),
        "--out",
        str(out_dir),
        "--profile",
        profile,
        "--article-profile",
        article_profile,
        "--y-scale",
        y_scale,
    ]
    if no_bonus:
        cmd_parts.append("--no-bonus")
    if ieee_ready:
        cmd_parts.append("--ieee-ready")
    if strict:
        cmd_parts.append("--strict")
    for token in scenario_filter_tokens:
        cmd_parts.extend(["--scenario-filter", token])

    def _quote_for_powershell(value: str) -> str:
        return '"' + value.replace('"', '`"') + '"'

    return " ".join(_quote_for_powershell(part) for part in cmd_parts)



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


def _top_campaign_errors(failures: list[dict[str, object]], *, limit: int = 3) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for failure in failures:
        error_type, message = _extract_error_payload(failure.get("error"))
        label = error_type
        if message:
            label = f"{error_type}: {message}"
        counter[label] += 1
    return counter.most_common(limit)


def _extract_error_payload(raw_error: object) -> tuple[str, str]:
    if isinstance(raw_error, str) and raw_error.strip():
        try:
            payload = json.loads(raw_error)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            error_type = str(payload.get("error_type", "UnknownError") or "UnknownError").strip() or "UnknownError"
            message = str(payload.get("message", "") or "").strip()
            return error_type, message
        return "UnknownError", raw_error.strip()
    if isinstance(raw_error, dict):
        error_type = str(raw_error.get("error_type", "UnknownError") or "UnknownError").strip() or "UnknownError"
        message = str(raw_error.get("message", "") or "").strip()
        return error_type, message
    return "UnknownError", ""


def _collect_batch_summary_errors(batch_summary: dict[str, object]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    failures = batch_summary.get("failures")
    if not isinstance(failures, list):
        return errors
    for failure in failures:
        if not isinstance(failure, dict):
            continue
        run_id = str(failure.get("run_id", "unknown"))
        error_type, message = _extract_error_payload(failure.get("error"))
        errors.append({"source": "batch_summary", "run_id": run_id, "type": error_type, "message": message})
    return errors


def _collect_campaign_log_errors(campaign_entries: list[dict[str, object]]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for entry in campaign_entries:
        run_id = str(entry.get("run_id", entry.get("step", "campaign")))
        for key in ("error", "exception", "message"):
            if key not in entry:
                continue
            error_type, message = _extract_error_payload(entry.get(key))
            if not message and key == "message":
                message = str(entry.get("message", "")).strip()
            if message:
                errors.append({"source": "campaign_log", "run_id": run_id, "type": error_type, "message": message})
                break
    return errors


def _collect_run_log_errors(run_logs: list[Path]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    pattern = re.compile(r"\|\s*ERROR\s*\|\s*(.+)$")
    for log_path in run_logs:
        run_id = log_path.parent.name
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            match = pattern.search(line)
            if match:
                message = match.group(1).strip()
                errors.append({"source": "run.log", "run_id": run_id, "type": "RuntimeError", "message": message})
    return errors


def _top_errors(entries: list[dict[str, str]], *, max_items: int = 10) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[str]] = {}
    for entry in entries:
        key = (entry.get("type", "UnknownError"), entry.get("message", ""))
        grouped.setdefault(key, []).append(entry.get("run_id", "unknown"))

    ordered = sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
    top: list[dict[str, object]] = []
    for (error_type, message), run_ids in ordered[:max_items]:
        top.append(
            {
                "type": error_type,
                "message": message,
                "frequency": len(run_ids),
                "example_run_ids": sorted(set(run_ids))[:5],
            }
        )
    return top


def _suggest_parameter_fixes(top_errors: list[dict[str, object]]) -> list[dict[str, str]]:
    corpus = " ".join(
        f"{item.get('type', '')} {item.get('message', '')}".lower()
        for item in top_errors
    )
    suggestions: list[dict[str, str]] = []

    if any(token in corpus for token in ["time_bin_s", "time bin", "tc", "comparabilit"]):
        suggestions.append(
            {
                "parameter": "time_bin_s",
                "suggested_value": "10",
                "rationale": "Utiliser 10s améliore la comparabilité de Tc et évite les bins trop fins/grossiers.",
            }
        )
    if any(token in corpus for token in ["duration_s", "walltime", "timeout", "max-walltime"]):
        suggestions.append(
            {
                "parameter": "duration_s",
                "suggested_value": "augmenter (ex: 3600)",
                "rationale": "Des erreurs de timeout/interruption suggèrent une durée de simulation trop courte.",
            }
        )
    if any(token in corpus for token in ["sf", "spreading", "sf-range"]):
        suggestions.append(
            {
                "parameter": "sf_range",
                "suggested_value": "7-12",
                "rationale": "Les erreurs SF peuvent venir d'une plage hors bornes LoRa standard.",
            }
        )
    if any(token in corpus for token in ["seed", "random", "negative"]):
        suggestions.append(
            {
                "parameter": "seed",
                "suggested_value": ">= 0",
                "rationale": "Utiliser un seed non négatif et stable améliore la reproductibilité.",
            }
        )

    if not suggestions and top_errors:
        most_common_type = Counter(str(item.get("type", "UnknownError")) for item in top_errors).most_common(1)[0][0]
        suggestions.append(
            {
                "parameter": "grid/params",
                "suggested_value": "valider la configuration",
                "rationale": f"Ajuster la grille autour des erreurs dominantes de type {most_common_type}.",
            }
        )
    return suggestions


def cmd_presets(args: argparse.Namespace) -> int:
    if args.list:
        for preset in list_presets():
            print(f"- {preset.name}: {preset.description}")
        return 0
    print("Aucune action demandée. Utiliser --list.")
    return 2


def cmd_diagnose(args: argparse.Namespace) -> int:
    results_dir: Path = args.results
    batch_summary_path = results_dir / "batch_summary.json"
    campaign_log_path = results_dir / "campaign_log.jsonl"
    run_logs = sorted((results_dir / "results").glob("*/run.log"))

    if not batch_summary_path.is_file():
        print(f"Erreur: batch_summary.json introuvable dans {results_dir}")
        return 2
    if not campaign_log_path.is_file():
        print(f"Erreur: campaign_log.jsonl introuvable dans {results_dir}")
        return 2

    batch_summary = json.loads(batch_summary_path.read_text(encoding="utf-8"))
    campaign_entries = [
        json.loads(line)
        for line in campaign_log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    error_entries = []
    error_entries.extend(_collect_batch_summary_errors(batch_summary))
    error_entries.extend(_collect_campaign_log_errors(campaign_entries))
    error_entries.extend(_collect_run_log_errors(run_logs))

    top = _top_errors(error_entries, max_items=args.top)
    suggestions = _suggest_parameter_fixes(top)

    print("Top erreurs détectées:")
    if not top:
        print("- Aucune erreur détectée dans les artefacts analysés.")
    for item in top:
        print(
            f"- [{item['frequency']}x] {item['type']} | {item['message'] or '(message vide)'} "
            f"| exemples run_id={','.join(item['example_run_ids'])}"
        )

    print("Corrections de paramètres proposées:")
    if not suggestions:
        print("- Aucune recommandation (aucune erreur exploitable).")
    for suggestion in suggestions:
        print(
            f"- {suggestion['parameter']} -> {suggestion['suggested_value']} "
            f"({suggestion['rationale']})"
        )

    report = {
        "results_dir": str(results_dir),
        "inputs": {
            "batch_summary": str(batch_summary_path),
            "campaign_log": str(campaign_log_path),
            "run_logs": [str(path) for path in run_logs],
        },
        "total_error_entries": len(error_entries),
        "top_errors": top,
        "parameter_suggestions": suggestions,
    }
    report_path = results_dir / "diagnostics_report.json"
    _dump_json(report_path, report)
    print(f"Rapport de diagnostic écrit: {report_path}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    inject_preset_args(args, project_dir=Path(__file__).resolve().parents[2])
    if not hasattr(args, "verbosity"):
        if getattr(args, "quiet", False):
            args.verbosity = 0
        elif getattr(args, "debug", False):
            args.verbosity = 3
        elif getattr(args, "verbose", False):
            args.verbosity = 2
        else:
            args.verbosity = 1

    try:
        if args.grid:
            grid_spec = args.grid
        elif args.profile:
            grid_spec = PROFILE_PRESETS[args.profile]
            print(f"Profil sélectionné: {args.profile}")
        else:
            raise SystemExit("Erreur: fournir --grid, --profile ou --preset.")

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
        "preset": getattr(getattr(args, "_preset", None), "name", None),
    }
    output_file = out_dir / "jobs.json"
    _dump_json(output_file, payload)

    from .simulator.engine import GridRunOrchestrator

    orchestrator = GridRunOrchestrator(output_root=out_dir)
    start_s = monotonic()

    progress_line_len = 0

    def _on_run_complete(run_report, run_i, total, success_count, failure_count, eta_s):
        nonlocal progress_line_len
        status = "OK" if run_report.success else "KO"
        line = (
            f"[{run_i}/{total}] {status} "
            f"succès={success_count} échecs={failure_count} ETA={_format_eta(eta_s)}"
        )
        pad = max(progress_line_len - len(line), 0)
        print("\r" + line + (" " * pad), end="", flush=True)
        progress_line_len = len(line)

    campaign_log_file = _campaign_log_path(out_dir, args.campaign_log)
    print(f"Run: progression des runs ({len(jobs)} au total).")

    report = orchestrator.execute_jobs(
        jobs,
        fail_fast=args.fail_fast,
        resume=args.resume,
        max_runs=args.max_runs,
        max_walltime_s=args.max_walltime,
        progress_interval_s=args.progress_interval,
        verbosity=args.verbosity,
        on_run_complete=_on_run_complete,
    )
    if report.reports:
        print()

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

    top_errors = _top_campaign_errors(failures, limit=3)
    print("Top-3 erreurs de la campagne:")
    if not top_errors:
        print("- Aucune")
    else:
        for label, count in top_errors:
            print(f"- {count}x | {label}")

    print(f"Résumé batch écrit dans {summary_file}")
    try:
        from .jamming.aggregate import aggregate_existing_results

        jamming_summary = aggregate_existing_results(
            out_dir, out_dir / "aggregate" / "campaign_summary.csv"
        )
        print(f"Résumé campagne de brouillage écrit dans {jamming_summary}")
    except FileNotFoundError:
        pass
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
    exit_code = 0

    try:
        from .jamming.aggregate import aggregate_existing_results

        jamming_summary = aggregate_existing_results(
            args.results[0] if len(args.results) == 1 else out_dir,
            out_dir / "aggregate" / "campaign_summary.csv",
        )
        if len(args.results) == 1:
            print(f"Résumé campagne de brouillage écrit dans {jamming_summary}")
    except FileNotFoundError:
        jamming_summary = None

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
        sinr_cdf_metadata: dict[str, object] = {}
        files = aggregate_runs(
            inputs=args.results,
            output_root=out_dir,
            summary_only=args.summary_only,
            skip_sinr_cdf=args.skip_sinr_cdf,
            skip_sf_distribution=args.skip_sf_distribution,
            strict=args.strict,
            verbose=args.verbose,
            verbose_warnings=args.verbose_warnings,
            sinr_quantile_step=args.sinr_quantile_step,
            sinr_cdf_granularity=args.sinr_cdf_granularity,
            ignored_runs_report=ignored_runs,
            sinr_cdf_metadata=sinr_cdf_metadata,
        )
    except (ValueError, json.JSONDecodeError, FileNotFoundError) as exc:
        if jamming_summary is not None:
            output_file = out_dir / "aggregate.json"
            _dump_json(
                output_file,
                {
                    "num_inputs": len(args.results),
                    "sources": [str(path) for path in args.results],
                    "jamming_campaign_summary": str(jamming_summary),
                },
            )
            print(f"Agrégation brouillage écrite dans {output_file}")
            return 0
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
    if jamming_summary is not None:
        manifest["jamming_campaign_summary"] = str(jamming_summary)

    metric_by_factor_path = files.get("metric_by_factor")
    distinct_groups_by_algo: dict[str, int] = {}
    if metric_by_factor_path is not None:
        with metric_by_factor_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                algo = str(row.get("algo", ""))
                distinct_groups_by_algo[algo] = distinct_groups_by_algo.get(algo, 0) + 1

    manifest["distinct_groups_by_algo"] = distinct_groups_by_algo
    manifest["sinr_cdf"] = sinr_cdf_metadata
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
    return exit_code


def cmd_plots(args: argparse.Namespace) -> int:
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    aggregates_dir = args.aggregates_dir or args.aggregates
    if aggregates_dir is None:
        print("Erreur: fournir --aggregates-dir (ou alias --aggregates).")
        return 2
    if (aggregates_dir / "aggregates").is_dir():
        aggregates_dir = aggregates_dir / "aggregates"

    from .plotting.plots import (
        ScenarioFilters,
        build_resume_commands,
        generate_minimal_figures,
        resolve_profile_behavior,
        validate_aggregates_inputs,
        validate_publication_context,
    )

    errors = validate_aggregates_inputs(aggregates_dir)
    if errors:
        print("Prérequis manquants pour plotting:")
        for err in errors:
            print(f"- {err}")
        print("Cause probable: l'agrégation n'a pas produit tous les CSV car une partie des runs a échoué ou est incomplète.")
        resume_cmds = build_resume_commands(aggregates_dir=aggregates_dir, out_dir=out_dir)
        print("Commandes de reprise recommandées:")
        print(f"- Run       : {resume_cmds['run']}")
        print(f"- Aggregate : {resume_cmds['aggregate']}")
        print(f"- Plots     : {resume_cmds['plots']}")
        return 2

    requested_filters = ScenarioFilters.from_tokens(args.scenario_filter)
    strict_context, facet_by = resolve_profile_behavior(
        profile=args.profile,
        strict_context=False,
        facet_by=(),
    )
    if args.profile == "publication":
        try:
            validate_publication_context(requested_filters)
        except ValueError as exc:
            print(f"Erreur: {exc}")
            return 2

    generated, traces = generate_minimal_figures(
        aggregates_dir=aggregates_dir,
        out_dir=out_dir,
        filters=requested_filters,
        article_profile=args.article_profile,
        include_bonus=not args.no_bonus,
        verbose=args.verbose,
        ieee_ready=args.ieee_ready,
        y_scale=args.y_scale,
        strict_context=strict_context,
        facet_by=facet_by,
        plot_profile=args.profile,
    )
    report = {
        "plot_profile": args.profile,
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
                "source_rows_read": trace.source_rows_read,
                "source_rows_usable": trace.source_rows_usable,
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
            f"| lignes_lues={trace.source_rows_read} | lignes_utilisables={trace.source_rows_usable} "
            f"| points={trace.num_points} | points/courbe={trace.points_by_curve}"
        )
    print(f"{len(generated)} figure(s) écrite(s) dans {out_dir}")
    diagnostics_file = out_dir / "plots_diagnostics.json"
    print(f"Résumé de plots écrit dans {output_file}")
    print(f"Diagnostic plots écrit dans {diagnostics_file}")

    exit_code = 0
    if len(generated) == 0:
        dominant_context = _dominant_context_from_plots_diagnostics(diagnostics_file)
        scenario_filter_tokens = _scenario_filter_resume_tokens(args.scenario_filter, dominant_context)
        resume_cmd = _build_plots_resume_command(
            aggregates_dir=aggregates_dir,
            out_dir=out_dir,
            profile=args.profile,
            article_profile=args.article_profile,
            no_bonus=args.no_bonus,
            ieee_ready=args.ieee_ready,
            y_scale=args.y_scale,
            strict=args.strict,
            scenario_filter_tokens=scenario_filter_tokens,
        )
        resume_cmd_powershell = _build_plots_resume_command_powershell(
            aggregates_dir=aggregates_dir,
            out_dir=out_dir,
            profile=args.profile,
            article_profile=args.article_profile,
            no_bonus=args.no_bonus,
            ieee_ready=args.ieee_ready,
            y_scale=args.y_scale,
            strict=args.strict,
            scenario_filter_tokens=scenario_filter_tokens,
        )
        print("Aucune figure générée : commandes de relance avec --scenario-filter basées sur le contexte dominant.")
        if dominant_context:
            print(
                "Contexte dominant détecté (via plots_diagnostics.json): "
                + ", ".join(f"{key}={value}" for key, value in dominant_context.items())
            )
        else:
            print("Contexte dominant non détecté dans plots_diagnostics.json (fallback sur filtres actuels).")
        print(f"Diagnostic à consulter: {diagnostics_file}")
        print(f"Commande (bash/zsh): {resume_cmd}")
        print(f"Exemple PowerShell direct: {resume_cmd_powershell}")
        print(f"Documentation: {PLOTS_NO_FIGURES_README_LINK}")
        exit_code = PLOTS_NO_FIGURES_EXIT_CODE

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
            "plots_diagnostics": str(diagnostics_file),
            "num_figures": len(generated),
            "figures": [
                {
                    "figure": trace.figure,
                    "source": trace.source,
                    "filters": trace.filters,
                    "num_points": trace.num_points,
                    "points_by_curve": trace.points_by_curve,
                    "source_rows_read": trace.source_rows_read,
                    "source_rows_usable": trace.source_rows_usable,
                    "generated": trace.generated,
                }
                for trace in traces
            ],
        },
    )
    print(f"Log campagne mis à jour: {campaign_log_file}")
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loraflexsim",
        description=(
            "CLI officielle `loraflexsim` pour les campagnes communauté (alias legacy : `mobilesfrdth`) : "
            "génération, agrégation, plots et validation. "
            "Les workflows avancés/spécialisés relèvent de `qos_cli` ou `pretest_campagne`; "
            "les anciens flux retirés sont décrits dans `docs/archive_or_research/`."
        ),
        epilog=(
            "Point d'entrée officiel recommandé : loraflexsim. Alias legacy : mobilesfrdth.\n"
            "CLI avancée / spécialisée : qos_cli / pretest_campagne. Archives : docs/archive_or_research, pretest_campagne/archive_or_mock/mobile-sfrd.\n"
            "Exemple grille: N=40,60,80,100,120,140,160,180,200;speed=1,3;reps=8;seed_base=1234\n"
            "Exemple run: loraflexsim run --config experiments/default.yaml --out runs --profile paper_core"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Génère les jobs puis exécute la campagne.")
    run_parser.add_argument(
        "--preset",
        choices=[preset.name for preset in list_presets()],
        default=None,
        help="Preset de campagne canonique (ex: paper_core, paper_fast, safe).",
    )
    run_parser.add_argument(
        "--config",
        required=False,
        type=_existing_file,
        help="Fichier de configuration de base. Optionnel si --preset fournit déjà la config.",
    )
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
    verbosity_group = run_parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("--quiet", action="store_true", help="Réduit les logs console au strict minimum.")
    verbosity_group.add_argument("--verbose", action="store_true", help="Augmente le niveau de logs de campagne.")
    verbosity_group.add_argument("--debug", action="store_true", help="Active les traces de debug détaillées (fichier run.log).")
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
        "--sinr-quantile-step",
        type=lambda value: _positive_float(value, name="--sinr-quantile-step"),
        default=0.05,
        help="[Compatibilité] Pas de discrétisation des quantiles SINR-CDF (préférer --sinr-cdf-granularity).",
    )
    aggregate_parser.add_argument(
        "--sinr-cdf-granularity",
        type=lambda value: _positive_float(value, name="--sinr-cdf-granularity"),
        default=None,
        help="Granularité CDF configurable pour SINR (pas de quantile, ex: 0.05).",
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
        "--verbose-warnings",
        action="store_true",
        help="Affiche chaque warning run-par-run en plus du résumé agrégé.",
    )
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
        "--profile",
        choices=PLOTS_PROFILE_CHOICES,
        default="exploratory",
        help="Profil de plotting: exploratory (auto contexte + facettes) ou publication (contexte strict obligatoire).",
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

    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Diagnostique les erreurs de campagne depuis batch_summary/campaign_log/run.log et propose des corrections.",
    )
    diagnose_parser.add_argument(
        "--results",
        required=True,
        type=_existing_path,
        help="Dossier de campagne contenant batch_summary.json, campaign_log.jsonl et results/*/run.log.",
    )
    diagnose_parser.add_argument(
        "--top",
        type=lambda value: _positive_int(value, name="--top"),
        default=10,
        help="Nombre maximum d'erreurs agrégées à afficher dans le top.",
    )
    diagnose_parser.set_defaults(func=cmd_diagnose)

    presets_parser = subparsers.add_parser("presets", help="Liste les presets de campagne disponibles.")
    presets_parser.add_argument("--list", action="store_true", help="Affiche les presets disponibles.")
    presets_parser.set_defaults(func=cmd_presets)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Valide la cohérence statistique et l'intégrité des agrégats CSV.",
    )
    validate_parser.add_argument(
        "--aggregates-dir",
        required=True,
        type=_existing_path,
        help="Répertoire aggregates/ contenant metric_by_factor.csv, convergence_tc.csv et sinr_cdf.csv.",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Retourne un code non-zéro si des warnings/erreurs QA sont détectés.",
    )
    validate_parser.set_defaults(func=cmd_validate)

    return parser



def cmd_validate(args: argparse.Namespace) -> int:
    from .qa.validate import validate_aggregates

    report = validate_aggregates(args.aggregates_dir)

    if report.errors:
        print("Validation QA: ERREURS")
        for issue in report.errors:
            print(f"- [ERREUR] {issue}")
    else:
        print("Validation QA: aucune erreur bloquante détectée.")

    if report.warnings:
        print("Validation QA: avertissements")
        for issue in report.warnings:
            print(f"- [WARN] {issue}")

    if args.strict and report.has_issues():
        return 2
    return 0

def _ensure_supported_python() -> bool:
    major, minor = sys.version_info[:2]
    return MIN_SUPPORTED_PYTHON <= (major, minor) < MAX_SUPPORTED_PYTHON_EXCLUSIVE


def main(argv: list[str] | None = None) -> int:
    if not _ensure_supported_python():
        print(
            "Version Python non supportée: utiliser une version >=3.11 et <3.13.",
            file=sys.stderr,
        )
        return 2

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if getattr(args, "command", None) == "run":
            if not getattr(args, "preset", None):
                if getattr(args, "config", None) is None:
                    raise ValueError("--config est obligatoire sans --preset.")
                if getattr(args, "grid", None) in (None, "") and getattr(args, "profile", None) is None:
                    raise ValueError("Fournir --grid ou --profile quand --preset n'est pas utilisé.")
            if args.quiet:
                args.verbosity = 0
            elif args.debug:
                args.verbosity = 3
            elif args.verbose:
                args.verbosity = 2
            else:
                args.verbosity = 1
        return args.func(args)
    except ValueError as exc:
        print(f"Erreur: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

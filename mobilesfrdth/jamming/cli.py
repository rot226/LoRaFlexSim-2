"""CLI dédiée aux campagnes de brouillage LoRaFlexSim."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import yaml

from .aggregate import aggregate_existing_results
from .campaigns import _jamming_windows, run_campaign
from .csv_exporter import write_run_csvs
from .jammer import JammerConfig
from .runner import run_jamming_simulation
from .scenarios import JammingScenario


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("la valeur doit être un entier") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("la valeur doit être > 0")
    return parsed


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("la valeur doit être un entier") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("la valeur doit être >= 0")
    return parsed


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("la valeur doit être un nombre") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("la valeur doit être > 0")
    return parsed


def _bool_token(value: str) -> bool:
    token = value.strip().lower()
    if token in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if token in {"0", "false", "no", "n", "off", "disabled"}:
        return False
    raise argparse.ArgumentTypeError("valeur attendue: on/off, true/false, yes/no ou 1/0")


def _csv_tokens(value: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in value.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("la liste ne doit pas être vide")
    return values


def _channels_hz(value: str) -> tuple[int, ...]:
    channels: list[int] = []
    for token in _csv_tokens(value):
        try:
            number = float(token)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"canal invalide: {token!r}") from exc
        channels.append(int(number * 1_000_000) if number < 10_000 else int(number))
    return tuple(channels)


def _load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with path.open(encoding="utf-8") as handle:
        if path.suffix.lower() == ".json":
            data = json.load(handle)
        else:
            data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("--config doit contenir un objet YAML/JSON au niveau racine.")
    return data


def _scenario_from_args(args: argparse.Namespace) -> JammingScenario:
    channels_hz = tuple(getattr(args, "channels", ()) or ())
    jammed_channel_hz = int(getattr(args, "jammed_channel", 0) or (channels_hz[0] if channels_hz else 868_100_000))
    jammers = tuple(
        JammerConfig(
            jammer_id=f"jammer_{index}",
            x_m=10.0 * index,
            y_m=0.0,
            channels_hz=(jammed_channel_hz,),
        )
        for index in range(1, 7)
    )
    return JammingScenario(
        name=args.scenario,
        jammers=jammers,
        metadata={
            "scenario_name": args.scenario,
            "sim_time_s": args.sim_time,
            "legitimate_channels_hz": channels_hz,
            "jammer_channels_hz": (jammed_channel_hz,),
            "jammed_channel_hz": jammed_channel_hz,
            "channel_selection": args.channel_selection,
            "time_bin_size": args.time_bin_size,
            "export_raw_events": args.export_raw_events,
        },
    )


def _common_options(parser: argparse.ArgumentParser, *, seed: bool = False, seeds: bool = False) -> None:
    parser.add_argument("--scenario", required=True, help="Nom du scénario de brouillage à exécuter.")
    parser.add_argument("--nodes", required=True, type=_positive_int, help="Nombre de nœuds légitimes.")
    parser.add_argument("--adr", required=True, type=_bool_token, help="Active ou désactive ADR (on/off).")
    if seed:
        parser.add_argument("--seed", required=True, type=_non_negative_int, help="Seed unique du run.")
    if seeds:
        parser.add_argument("--seeds", required=True, help="Seeds de campagne: liste 1,2,3 ou plage inclusive 1:10.")
    parser.add_argument("--sim-time", required=True, type=_positive_float, help="Durée simulée en secondes.")
    parser.add_argument("--channels", required=True, type=_channels_hz, help="Canaux légitimes, séparés par des virgules (Hz ou MHz).")
    parser.add_argument("--jammed-channel", required=True, type=lambda v: _channels_hz(v)[0], help="Canal brouillé unique (Hz ou MHz).")
    parser.add_argument("--channel-selection", required=True, help="Politique de sélection de canal.")
    parser.add_argument(
        "--allow-channel-selection-without-adr",
        action="store_true",
        help="Autorise une politique de canal dynamique même quand --adr est désactivé.",
    )
    parser.add_argument("--out", required=True, type=Path, help="Répertoire de sortie.")
    parser.add_argument("--resume", action="store_true", help="Reprend les sorties complètes déjà présentes.")
    parser.add_argument("--overwrite", action="store_true", help="Réécrit les sorties existantes.")
    parser.add_argument("--dry-run", action="store_true", help="Affiche le plan sans exécuter de simulation.")
    parser.add_argument("--export-raw-events", action="store_true", help="Conserve l'export des événements bruts si disponible.")
    parser.add_argument("--time-bin-size", required=True, type=_positive_float, help="Taille des bins temporels en secondes.")
    parser.add_argument("--config", type=Path, help="Fichier YAML/JSON optionnel à recopier dans la sortie.")


def cmd_run(args: argparse.Namespace) -> int:
    if args.channel_selection != "static" and not args.adr and not args.allow_channel_selection_without_adr:
        raise ValueError("--allow-channel-selection-without-adr est requis pour utiliser --channel-selection sans ADR.")
    config = _load_config(args.config)
    scenario = _scenario_from_args(args)
    if args.dry_run:
        print(f"Dry-run: 1 run scenario={args.scenario} nodes={args.nodes} adr={args.adr} seed={args.seed}")
        return 0
    if args.out.exists() and any(args.out.iterdir()) and not args.overwrite and not args.resume:
        raise ValueError(f"Le répertoire de sortie existe déjà et n'est pas vide: {args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    result = run_jamming_simulation(
        node_count=args.nodes,
        until_s=args.sim_time,
        seed=args.seed,
        jamming_windows=_jamming_windows(scenario, seed=args.seed),
        algo="adr" if args.adr else "none",
    )
    result.run_summary.update(
        {
            "scenario": scenario.name,
            "scenario_name": scenario.name,
            "nodes": args.nodes,
            "node_count": args.nodes,
            "adr": "on" if args.adr else "off",
            "adr_enabled": args.adr,
            "seed": args.seed,
            "channel_selection": args.channel_selection,
            "jammed_channel_hz": args.jammed_channel,
            "time_bin_size": args.time_bin_size,
        }
    )
    write_run_csvs(result, {"root": args.out, "raw": args.out / "raw", "per_run": args.out / "per_run"})
    (args.out / "config_used.yaml").write_text(yaml.safe_dump({**config, "scenario": scenario.to_dict()}, allow_unicode=True), encoding="utf-8")
    print(f"Run jamming terminé: {args.out}")
    return 0


def cmd_campaign(args: argparse.Namespace) -> int:
    if args.channel_selection != "static" and not args.adr and not args.allow_channel_selection_without_adr:
        raise ValueError("--allow-channel-selection-without-adr est requis pour utiliser --channel-selection sans ADR.")
    config = _load_config(args.config)
    scenario = _scenario_from_args(args)
    run_campaign(
        layout=args.out,
        scenarios=(scenario,),
        node_counts=(args.nodes,),
        seeds=args.seeds,
        adr_modes=(args.adr,),
        channel_selections=(args.channel_selection,),
        resume=args.resume,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        config={**config, "channels_hz": args.channels, "jammed_channel_hz": args.jammed_channel, "time_bin_size": args.time_bin_size},
    )
    return 0


def cmd_aggregate(args: argparse.Namespace) -> int:
    output = aggregate_existing_results(args.input, args.output)
    print(f"Agrégation jamming écrite: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loraflexsim", description="CLI jamming LoRaFlexSim.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Exécute un run de brouillage avec une seed unique.")
    _common_options(run_parser, seed=True)
    run_parser.set_defaults(func=cmd_run)

    campaign_parser = subparsers.add_parser("campaign", help="Exécute une campagne de brouillage multi-seeds.")
    _common_options(campaign_parser, seeds=True)
    campaign_parser.set_defaults(func=cmd_campaign)

    aggregate_parser = subparsers.add_parser("aggregate", help="Agrège des résultats de brouillage existants.")
    aggregate_parser.add_argument("--input", required=True, type=Path, help="Dossier ou CSV run_summary.csv en entrée.")
    aggregate_parser.add_argument("--output", required=True, type=Path, help="CSV agrégé à écrire.")
    aggregate_parser.set_defaults(func=cmd_aggregate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except ValueError as exc:
        print(f"Erreur: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

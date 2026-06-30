"""CLI dédiée aux campagnes de brouillage LoRaFlexSim."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

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
    raise argparse.ArgumentTypeError(
        "valeur attendue: on/off, true/false, yes/no ou 1/0"
    )


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


def _format_seconds(value: Any) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.1f}"


def _make_progress_writer() -> tuple[Callable[[str], None], Callable[[], None]]:
    interactive = sys.stdout.isatty()
    last_len = 0

    def write(line: str) -> None:
        nonlocal last_len
        if interactive:
            padding = " " * max(last_len - len(line), 0)
            sys.stdout.write("\r" + line + padding)
            sys.stdout.flush()
            last_len = len(line)
        else:
            print(line)

    def finish() -> None:
        nonlocal last_len
        if interactive and last_len:
            sys.stdout.write("\n")
            sys.stdout.flush()
            last_len = 0

    return write, finish


def _should_emit_progress(
    progress_pct: float, state: dict[str, float], step: float
) -> bool:
    if progress_pct >= 100.0:
        state["last_pct"] = 100.0
        return True
    last_pct = state.get("last_pct")
    if last_pct is None or progress_pct - last_pct >= step:
        state["last_pct"] = progress_pct
        return True
    return False


def _format_run_progress(
    prefix: str, progress_pct: float, context: dict[str, Any]
) -> str:
    return (
        f"{prefix} : {progress_pct:.1f} % | "
        f"t={_format_seconds(context.get('time_s', 0.0))}/{_format_seconds(context.get('until_s', 0.0))} s | "
        f"tx={context.get('tx_packets', 0)} | "
        f"rx={context.get('rx_packets', 0)} | "
        f"jammed={context.get('jammed_packets', 0)}"
    )


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


def _option_dests(parser: argparse.ArgumentParser) -> dict[str, str]:
    option_dests: dict[str, str] = {}
    parsers = [parser]
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            parsers.extend(
                choice
                for choice in choices.values()
                if isinstance(choice, argparse.ArgumentParser)
            )
    for current_parser in parsers:
        for action in current_parser._actions:
            for option in action.option_strings:
                if option.startswith("--"):
                    option_dests[option] = action.dest
    return option_dests


def _cli_supplied_dests(
    parser: argparse.ArgumentParser, argv: Sequence[str]
) -> set[str]:
    option_dests = _option_dests(parser)
    supplied: set[str] = set()
    for token in argv:
        option = token.split("=", 1)[0]
        if option in option_dests:
            supplied.add(option_dests[option])
    return supplied


def _first_config_value(config: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in config:
            return config[key]
    return None


def _coerce_channels(value: Any) -> tuple[int, ...]:
    if isinstance(value, str):
        return _channels_hz(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(_channels_hz(str(item))[0] for item in value)
    return _channels_hz(str(value))


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _bool_token(str(value))


def _merge_config_args(
    args: argparse.Namespace, cli_supplied: set[str]
) -> argparse.Namespace:
    config = _load_config(getattr(args, "config", None))
    mappings: dict[str, tuple[str, ...]] = {
        "scenario": ("scenario", "scenario_name"),
        "nodes": ("nodes", "node_count", "node_counts"),
        "adr": ("adr", "adr_enabled"),
        "seed": ("seed",),
        "seeds": ("seeds",),
        "sim_time": ("sim_time", "sim_time_s"),
        "channels": (
            "channels",
            "channels_hz",
            "channels_mhz",
            "legitimate_channels_hz",
            "legitimate_channels_mhz",
        ),
        "jammed_channel": ("jammed_channel", "jammed_channel_hz", "jammed_channel_mhz"),
        "channel_selection": ("channel_selection",),
        "out": ("out", "output", "output_dir"),
        "time_bin_size": ("time_bin_size", "time_bin_size_s"),
        "export_raw_events": ("export_raw_events",),
        "allow_channel_selection_without_adr": ("allow_channel_selection_without_adr",),
    }
    for dest, keys in mappings.items():
        if dest in cli_supplied or getattr(args, dest, None) not in (None, False):
            continue
        value = _first_config_value(config, *keys)
        if value is None:
            continue
        if dest == "channels":
            value = _coerce_channels(value)
        elif dest == "jammed_channel":
            value = _coerce_channels(value)[0]
        elif dest in {
            "adr",
            "export_raw_events",
            "allow_channel_selection_without_adr",
        }:
            value = _coerce_bool(value)
        elif dest == "nodes":
            if isinstance(value, Sequence) and not isinstance(
                value, (str, bytes, bytearray)
            ):
                value = (
                    tuple(int(item) for item in value)
                    if hasattr(args, "seeds")
                    else int(value[0])
                )
            else:
                value = int(value)
        elif dest == "seed":
            if isinstance(value, Sequence) and not isinstance(
                value, (str, bytes, bytearray)
            ):
                value = value[0]
            value = int(value)
        elif dest == "sim_time" or dest == "time_bin_size":
            value = float(value)
        elif dest == "out":
            value = Path(value)
        setattr(args, dest, value)
    _validate_required_args(args)
    return args


def _validate_required_args(args: argparse.Namespace) -> None:
    required = [
        "scenario",
        "nodes",
        "adr",
        "sim_time",
        "channels",
        "jammed_channel",
        "channel_selection",
        "out",
        "time_bin_size",
    ]
    if hasattr(args, "seed"):
        required.append("seed")
    if hasattr(args, "seeds"):
        required.append("seeds")
    missing = [dest for dest in required if getattr(args, dest, None) is None]
    if missing:
        options = ", ".join(f"--{dest.replace('_', '-')}" for dest in missing)
        raise ValueError(f"Arguments manquants après fusion config + CLI: {options}.")


def _scenario_from_args(args: argparse.Namespace) -> JammingScenario:
    channels_hz = tuple(getattr(args, "channels", ()) or ())
    jammed_channel_hz = int(
        getattr(args, "jammed_channel", 0)
        or (channels_hz[0] if channels_hz else 868_100_000)
    )
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


def _common_options(
    parser: argparse.ArgumentParser, *, seed: bool = False, seeds: bool = False
) -> None:
    parser.add_argument("--scenario", help="Nom du scénario de brouillage à exécuter.")
    parser.add_argument(
        "--nodes", type=_positive_int, help="Nombre de nœuds légitimes."
    )
    parser.add_argument(
        "--adr", type=_bool_token, help="Active ou désactive ADR (on/off)."
    )
    if seed:
        parser.add_argument(
            "--seed", type=_non_negative_int, help="Seed unique du run."
        )
    if seeds:
        parser.add_argument(
            "--seeds", help="Seeds de campagne: liste 1,2,3 ou plage inclusive 1:10."
        )
    parser.add_argument(
        "--sim-time", type=_positive_float, help="Durée simulée en secondes."
    )
    parser.add_argument(
        "--channels",
        type=_channels_hz,
        help="Canaux légitimes, séparés par des virgules (Hz ou MHz).",
    )
    parser.add_argument(
        "--jammed-channel",
        type=lambda v: _channels_hz(v)[0],
        help="Canal brouillé unique (Hz ou MHz).",
    )
    parser.add_argument("--channel-selection", help="Politique de sélection de canal.")
    parser.add_argument(
        "--allow-channel-selection-without-adr",
        action="store_true",
        help="Autorise une politique de canal dynamique même quand --adr est désactivé.",
    )
    parser.add_argument("--out", type=Path, help="Répertoire de sortie.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reprend les sorties complètes déjà présentes.",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Réécrit les sorties existantes."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche le plan sans exécuter de simulation.",
    )
    parser.add_argument(
        "--export-raw-events",
        action="store_true",
        help="Conserve l'export des événements bruts si disponible.",
    )
    parser.add_argument(
        "--time-bin-size",
        type=_positive_float,
        help="Taille des bins temporels en secondes.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Fichier YAML/JSON optionnel à recopier dans la sortie.",
    )
    parser.add_argument(
        "--progress",
        dest="progress",
        action="store_true",
        default=True,
        help="Affiche la progression pendant l'exécution (activé par défaut).",
    )
    parser.add_argument(
        "--no-progress",
        dest="progress",
        action="store_false",
        help="Désactive l'affichage de progression.",
    )
    parser.add_argument(
        "--progress-step",
        type=_positive_float,
        default=5.0,
        help="Pas d'affichage de la progression en pourcentage (défaut: 5.0).",
    )


def cmd_run(args: argparse.Namespace) -> int:
    if (
        args.channel_selection != "static"
        and not args.adr
        and not args.allow_channel_selection_without_adr
    ):
        raise ValueError(
            "--allow-channel-selection-without-adr est requis pour utiliser --channel-selection sans ADR."
        )
    config = _load_config(args.config)
    scenario = _scenario_from_args(args)
    if args.dry_run:
        print(
            f"Dry-run: 1 run scenario={args.scenario} nodes={args.nodes} adr={args.adr} seed={args.seed}"
        )
        return 0
    if (
        args.out.exists()
        and any(args.out.iterdir())
        and not args.overwrite
        and not args.resume
    ):
        raise ValueError(
            f"Le répertoire de sortie existe déjà et n'est pas vide: {args.out}"
        )
    args.out.mkdir(parents=True, exist_ok=True)
    progress_finish: Callable[[], None] | None = None
    progress_callback: Callable[[float, dict], None] | None = None
    if args.progress:
        write_progress, progress_finish = _make_progress_writer()
        progress_state: dict[str, float] = {}
        prefix = f"Run {scenario.name} seed={args.seed}"

        def progress_callback(progress: float, context: dict) -> None:
            progress_pct = min(max(float(progress) * 100.0, 0.0), 100.0)
            if _should_emit_progress(progress_pct, progress_state, args.progress_step):
                write_progress(_format_run_progress(prefix, progress_pct, context))

    try:
        result = run_jamming_simulation(
            node_count=args.nodes,
            until_s=args.sim_time,
            seed=args.seed,
            jamming_windows=_jamming_windows(scenario, seed=args.seed),
            algo="adr" if args.adr else "none",
            progress_callback=progress_callback,
        )
    finally:
        if progress_finish is not None:
            progress_finish()
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
    write_run_csvs(
        result,
        {"root": args.out, "raw": args.out / "raw", "per_run": args.out / "per_run"},
    )
    (args.out / "config_used.yaml").write_text(
        yaml.safe_dump({**config, "scenario": scenario.to_dict()}, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Run jamming terminé: {args.out}")
    return 0


def cmd_campaign(args: argparse.Namespace) -> int:
    if (
        args.channel_selection != "static"
        and not args.adr
        and not args.allow_channel_selection_without_adr
    ):
        raise ValueError(
            "--allow-channel-selection-without-adr est requis pour utiliser --channel-selection sans ADR."
        )
    config = _load_config(args.config)
    scenario = _scenario_from_args(args)
    progress_finish: Callable[[], None] | None = None
    campaign_progress_callback = None
    if args.progress and not args.dry_run:
        write_progress, progress_finish = _make_progress_writer()
        progress_state: dict[str, float] = {}

        def campaign_progress_callback(
            run_key: Any,
            run_index: int,
            total_runs: int,
            progress: float,
            context: dict[str, Any],
        ) -> None:
            run_pct = min(max(float(progress) * 100.0, 0.0), 100.0)
            global_pct = (
                (float(run_index - 1) + float(progress)) / max(total_runs, 1) * 100.0
            )
            if _should_emit_progress(global_pct, progress_state, args.progress_step):
                write_progress(
                    f"Campagne : run {run_index}/{total_runs} | "
                    f"{global_pct:.1f} % global | run courant {run_pct:.1f} %"
                )

    try:
        run_campaign(
            layout=args.out,
            scenarios=(scenario,),
            node_counts=(
                args.nodes
                if isinstance(args.nodes, Sequence)
                and not isinstance(args.nodes, (str, bytes, bytearray))
                else (args.nodes,)
            ),
            seeds=args.seeds,
            adr_modes=(args.adr,),
            channel_selections=(args.channel_selection,),
            resume=args.resume,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            config={
                **config,
                "channels_hz": args.channels,
                "jammed_channel_hz": args.jammed_channel,
                "time_bin_size": args.time_bin_size,
            },
            progress_callback=campaign_progress_callback,
        )
    finally:
        if progress_finish is not None:
            progress_finish()
    return 0


def cmd_aggregate(args: argparse.Namespace) -> int:
    output = aggregate_existing_results(args.input, args.output)
    print(f"Agrégation jamming écrite: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loraflexsim", description="CLI jamming LoRaFlexSim."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="Exécute un run de brouillage avec une seed unique."
    )
    _common_options(run_parser, seed=True)
    run_parser.set_defaults(func=cmd_run)

    campaign_parser = subparsers.add_parser(
        "campaign", help="Exécute une campagne de brouillage multi-seeds."
    )
    _common_options(campaign_parser, seeds=True)
    campaign_parser.set_defaults(func=cmd_campaign)

    aggregate_parser = subparsers.add_parser(
        "aggregate",
        help=(
            "Recalcule uniquement l'agrégat depuis les run_summary.csv existants; "
            "ne complète pas les métriques manquantes."
        ),
    )
    aggregate_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help=(
            "Dossier ou CSV run_summary.csv existant en entrée. "
            "La commande ne régénère aucun CSV brut ni métrique manquante."
        ),
    )
    aggregate_parser.add_argument(
        "--output", required=True, type=Path, help="CSV agrégé à écrire."
    )
    aggregate_parser.set_defaults(func=cmd_aggregate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        raw_argv = tuple(argv) if argv is not None else tuple(sys.argv[1:])
        args = parser.parse_args(argv)
        args = _merge_config_args(args, _cli_supplied_dests(parser, raw_argv))
        return args.func(args)
    except ValueError as exc:
        print(f"Erreur: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

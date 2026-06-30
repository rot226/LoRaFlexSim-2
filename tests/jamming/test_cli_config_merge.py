from __future__ import annotations

from pathlib import Path

from mobilesfrdth.jamming.cli import (
    _cli_supplied_dests,
    _merge_config_args,
    build_parser,
)


def _parse(argv: list[str]):
    parser = build_parser()
    args = parser.parse_args(argv)
    return _merge_config_args(args, _cli_supplied_dests(parser, argv))


def test_campaign_config_populates_arguments_from_yaml() -> None:
    args = _parse(
        [
            "campaign",
            "--config",
            "config/jamming/baseline_single_channel.yaml",
            "--out",
            "runs/jamming-baseline",
            "--dry-run",
        ]
    )

    assert args.scenario == "baseline_single_channel"
    assert args.nodes == (20, 50, 100)
    assert args.seeds == "0:49"
    assert args.sim_time == 3600.0
    assert args.channels == (868_100_000,)
    assert args.jammed_channel == 868_100_000
    assert args.channel_selection == "static"
    assert args.adr == (False,)
    assert args.out == Path("runs/jamming-baseline")


def test_cli_arguments_override_config_values() -> None:
    args = _parse(
        [
            "campaign",
            "--config",
            "config/jamming/multichannel_adr_selection.yaml",
            "--nodes",
            "50",
            "--channels",
            "868.3",
            "--adr",
            "off",
            "--out",
            "runs/jamming-multichannel",
            "--dry-run",
        ]
    )

    assert args.nodes == (50,)
    assert args.channels == (868_300_000,)
    assert args.adr == (False,)
    assert args.jammed_channel == 868_100_000

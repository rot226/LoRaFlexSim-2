from __future__ import annotations

from pathlib import Path

from mobilesfrdth.jamming import cli


def _campaign_args(tmp_path: Path, *extra: str) -> list[str]:
    return [
        "campaign",
        "--scenario",
        "smoke",
        "--nodes",
        "2",
        "--adr",
        "on",
        "--seeds",
        "0:49",
        "--sim-time",
        "1",
        "--channels",
        "868.1",
        "--jammed-channel",
        "868.1",
        "--channel-selection",
        "static",
        "--out",
        str(tmp_path),
        "--time-bin-size",
        "1",
        *extra,
    ]


def test_campaign_cli_parses_seed_range_in_dry_run(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(_campaign_args(tmp_path, "--dry-run"))

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Plan dry-run: 50 run(s)" in output
    assert "seed=0" in output
    assert "seed=49" in output
    assert not any(tmp_path.iterdir())


def test_campaign_cli_forwards_resume_without_long_simulation(
    tmp_path: Path, monkeypatch
) -> None:
    calls = []

    def fake_run_campaign(**kwargs):
        calls.append(kwargs)
        return ()

    monkeypatch.setattr(cli, "run_campaign", fake_run_campaign)

    exit_code = cli.main(_campaign_args(tmp_path, "--resume"))

    assert exit_code == 0
    assert calls
    assert calls[0]["resume"] is True
    assert calls[0]["dry_run"] is False
    assert calls[0]["seeds"] == "0:49"
    assert calls[0]["node_counts"] == (2,)


def test_campaign_cli_accepts_comma_separated_nodes(
    tmp_path: Path, monkeypatch
) -> None:
    calls = []

    def fake_run_campaign(**kwargs):
        calls.append(kwargs)
        return ()

    monkeypatch.setattr(cli, "run_campaign", fake_run_campaign)

    exit_code = cli.main(_campaign_args(tmp_path, "--nodes", "20,50,100"))

    assert exit_code == 0
    assert calls[0]["node_counts"] == (20, 50, 100)


def test_campaign_cli_accepts_adr_both(tmp_path: Path, monkeypatch) -> None:
    calls = []

    def fake_run_campaign(**kwargs):
        calls.append(kwargs)
        return ()

    monkeypatch.setattr(cli, "run_campaign", fake_run_campaign)

    exit_code = cli.main(_campaign_args(tmp_path, "--adr", "both"))

    assert exit_code == 0
    assert calls[0]["adr_modes"] == (True, False)


def test_campaign_cli_combines_nodes_adr_both_and_seed_range(
    tmp_path: Path, monkeypatch
) -> None:
    calls = []

    def fake_run_campaign(**kwargs):
        calls.append(kwargs)
        return ()

    monkeypatch.setattr(cli, "run_campaign", fake_run_campaign)

    exit_code = cli.main(
        _campaign_args(
            tmp_path,
            "--nodes",
            "20,50,100",
            "--adr",
            "both",
            "--seeds",
            "0:49",
        )
    )

    assert exit_code == 0
    assert calls[0]["node_counts"] == (20, 50, 100)
    assert calls[0]["adr_modes"] == (True, False)
    assert calls[0]["seeds"] == "0:49"

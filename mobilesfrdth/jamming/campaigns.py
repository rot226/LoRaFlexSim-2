"""Construction et exécution de campagnes de brouillage reproductibles."""

from __future__ import annotations

import json
import random
import shlex
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

import yaml

from .aggregate import aggregate_existing_results
from .csv_exporter import write_run_csvs
from .jammer import JammingEvent
from .placement import circle_placement, grid_placement, random_placement
from .runner import run_jamming_simulation
from .scenarios import DEFAULT_SIM_TIME_S, JammingScenario

EXPECTED_RUN_CSVS = (
    "per_run/run_summary.csv",
    "raw/node_metrics_*.csv",
    "raw/channel_timeseries_*.csv",
    "raw/sf_timeseries_*.csv",
)


@dataclass(frozen=True)
class JammingCampaign:
    """Collection nommée de scénarios de brouillage."""

    name: str
    scenarios: tuple[JammingScenario, ...]


@dataclass(frozen=True)
class JammingRunKey:
    """Identifiant stable d'un run de campagne de brouillage."""

    scenario: str
    node_count: int
    adr_enabled: bool
    seed: int
    channel_selection: str

    @property
    def run_id(self) -> str:
        adr = "on" if self.adr_enabled else "off"
        return f"{_safe_token(self.scenario)}_n{self.node_count}_adr_{adr}_seed_{self.seed}_ch_{_safe_token(self.channel_selection)}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"run_id": self.run_id}


@dataclass(frozen=True)
class CampaignLayout:
    """Arborescence d'une campagne de brouillage."""

    root: Path

    @property
    def runs_dir(self) -> Path:
        return self.root / "runs"

    @property
    def aggregate_dir(self) -> Path:
        return self.root / "aggregate"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    def run_dir(self, run_key: JammingRunKey) -> Path:
        return self.runs_dir / run_key.run_id


def parse_seed_spec(value: str | Sequence[int]) -> tuple[int, ...]:
    """Analyse une spécification de seeds.

    Formats supportés: ``"0:49"`` (bornes incluses) et ``"0,1,2,3"``.
    """

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("La spécification des seeds ne doit pas être vide.")
        if ":" in text:
            if text.count(":") != 1:
                raise ValueError("Format seed attendu: début:fin, par exemple 0:49.")
            left, right = (part.strip() for part in text.split(":", 1))
            start, end = _parse_non_negative_int(left, "seed début"), _parse_non_negative_int(right, "seed fin")
            if end < start:
                raise ValueError("La borne finale des seeds doit être >= à la borne initiale.")
            return tuple(range(start, end + 1))
        seeds = tuple(_parse_non_negative_int(part.strip(), "seed") for part in text.split(",") if part.strip())
    else:
        seeds = tuple(int(seed) for seed in value)
    if not seeds:
        raise ValueError("Au moins une seed est requise.")
    if any(seed < 0 for seed in seeds):
        raise ValueError("Les seeds doivent être >= 0.")
    return seeds


def parse_nodes_spec(value: str | Sequence[int]) -> tuple[int, ...]:
    """Analyse une liste de nombres de nœuds, par exemple ``"20,50,100"``."""

    if isinstance(value, str):
        nodes = tuple(_parse_positive_int(part.strip(), "node_count") for part in value.split(",") if part.strip())
    else:
        nodes = tuple(int(node) for node in value)
    if not nodes:
        raise ValueError("Au moins un nombre de nœuds est requis.")
    if any(node <= 0 for node in nodes):
        raise ValueError("Les nombres de nœuds doivent être > 0.")
    return nodes


def expand_adr_modes(value: str | bool | Sequence[bool]) -> tuple[bool, ...]:
    """Développe ``on``, ``off`` ou ``both`` en booléens ADR."""

    if isinstance(value, str):
        text = value.strip().lower()
        if text == "on":
            return (True,)
        if text == "off":
            return (False,)
        if text == "both":
            return (True, False)
        raise ValueError('adr_modes doit valoir "on", "off" ou "both".')
    if isinstance(value, bool):
        return (value,)
    modes = tuple(bool(item) for item in value)
    if not modes:
        raise ValueError("Au moins un mode ADR est requis.")
    return modes


def expand_run_matrix(
    *,
    scenarios: Iterable[JammingScenario | str],
    node_counts: Iterable[int],
    adr_modes: Iterable[bool],
    seeds: Iterable[int],
    channel_selections: Iterable[str],
) -> tuple[JammingRunKey, ...]:
    """Génère la matrice ``(scenario, node_count, adr_enabled, seed, channel_selection)``."""

    scenario_names = tuple(scenario.name if isinstance(scenario, JammingScenario) else str(scenario) for scenario in scenarios)
    nodes = tuple(int(value) for value in node_counts)
    adrs = tuple(bool(value) for value in adr_modes)
    seed_values = tuple(int(value) for value in seeds)
    selections = tuple(str(value) for value in channel_selections)
    if not all((scenario_names, nodes, adrs, seed_values, selections)):
        raise ValueError("La matrice de runs ne peut pas contenir de dimension vide.")
    return tuple(
        JammingRunKey(scenario, node_count, adr_enabled, seed, channel_selection)
        for scenario in scenario_names
        for node_count in nodes
        for adr_enabled in adrs
        for seed in seed_values
        for channel_selection in selections
    )


def dry_run_plan(runs: Iterable[JammingRunKey], *, stream: TextIO | None = None) -> None:
    """Affiche tous les runs planifiés sans exécution."""

    output = stream or sys.stdout
    run_list = tuple(runs)
    print(f"Plan dry-run: {len(run_list)} run(s)", file=output)
    for index, run_key in enumerate(run_list, start=1):
        print(
            f"{index:04d} | scenario={run_key.scenario} | nodes={run_key.node_count} | "
            f"adr={'on' if run_key.adr_enabled else 'off'} | seed={run_key.seed} | "
            f"channel_selection={run_key.channel_selection} | run_id={run_key.run_id}",
            file=output,
        )


def is_run_complete(layout: CampaignLayout | str | Path | Mapping[str, Any], run_key: JammingRunKey) -> bool:
    """Vérifie les CSV attendus et un statut ``completed`` pour un run."""

    run_dir = _coerce_layout(layout).run_dir(run_key)
    status_path = run_dir / "status.json"
    if not status_path.is_file():
        return False
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if status.get("status") != "completed":
        return False
    for relative in EXPECTED_RUN_CSVS:
        matches = list((run_dir / Path(relative).parent).glob(Path(relative).name))
        if not any(path.is_file() for path in matches):
            return False
    return True


def run_campaign(
    *,
    layout: CampaignLayout | str | Path,
    scenarios: Sequence[JammingScenario],
    node_counts: str | Sequence[int] = "20,50,100",
    seeds: str | Sequence[int] = "0:49",
    adr_modes: str | Sequence[bool] = "both",
    channel_selections: Sequence[str] = ("static", "adr-assisted"),
    resume: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
    config: Mapping[str, Any] | None = None,
) -> tuple[JammingRunKey, ...]:
    """Exécute une campagne complète puis lance l'agrégation finale."""

    campaign_layout = _coerce_layout(layout)
    runs = expand_run_matrix(
        scenarios=scenarios,
        node_counts=parse_nodes_spec(node_counts),
        adr_modes=expand_adr_modes(adr_modes),
        seeds=parse_seed_spec(seeds),
        channel_selections=channel_selections,
    )
    if dry_run:
        dry_run_plan(runs)
        return runs

    campaign_layout.root.mkdir(parents=True, exist_ok=True)
    campaign_layout.logs_dir.mkdir(parents=True, exist_ok=True)
    _write_campaign_metadata(campaign_layout, runs, config=config)
    scenario_by_name = {scenario.name: scenario for scenario in scenarios}
    for run_key in runs:
        if resume and not overwrite and is_run_complete(campaign_layout, run_key):
            _log(campaign_layout, "skip_completed", run_key=run_key.to_dict())
            continue
        if overwrite:
            _log(campaign_layout, "overwrite", run_key=run_key.to_dict())
        _execute_run(campaign_layout, scenario_by_name[run_key.scenario], run_key)
    aggregate_existing_results(campaign_layout.runs_dir, campaign_layout.aggregate_dir / "campaign_summary.csv")
    _log(campaign_layout, "aggregate_completed", path=str(campaign_layout.aggregate_dir / "campaign_summary.csv"))
    return runs


def build_campaign(
    *,
    name: str,
    jammer_counts: tuple[int, ...],
    area_size_m: float,
    placement: str = "grid",
    seed: int | None = None,
    gateway_x: float | None = None,
    gateway_y: float | None = None,
    jammer_radius_m: float = 10.0,
    start_angle_deg: float = 0.0,
) -> JammingCampaign:
    """Crée une campagne en variant le nombre de brouilleurs."""

    scenarios: list[JammingScenario] = []
    for count in jammer_counts:
        if placement == "random":
            configs = random_placement(count=count, area_size_m=area_size_m, seed=None if seed is None else seed + count)
        elif placement == "grid":
            configs = grid_placement(count=count, area_size_m=area_size_m)
        elif placement == "circle":
            center_x = area_size_m / 2 if gateway_x is None else gateway_x
            center_y = area_size_m / 2 if gateway_y is None else gateway_y
            configs = circle_placement(gateway_x=center_x, gateway_y=center_y, radius_m=jammer_radius_m, count=count, start_angle_deg=start_angle_deg)
        else:
            raise ValueError("placement doit valoir 'grid', 'random' ou 'circle'.")
        scenarios.append(JammingScenario(name=f"{name}_jammers_{count}", jammers=tuple(configs), metadata={"placement": placement}))
    return JammingCampaign(name=name, scenarios=tuple(scenarios))


def _execute_run(layout: CampaignLayout, scenario: JammingScenario, run_key: JammingRunKey) -> None:
    run_dir = layout.run_dir(run_key)
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / "status.json"
    status_path.write_text(json.dumps({"status": "running", "run_key": run_key.to_dict()}, indent=2), encoding="utf-8")
    windows = _jamming_windows(scenario, seed=run_key.seed)
    result = run_jamming_simulation(
        node_count=run_key.node_count,
        until_s=float(scenario.metadata.get("sim_time_s", DEFAULT_SIM_TIME_S)),
        seed=run_key.seed,
        jamming_windows=windows,
        algo="adr" if run_key.adr_enabled else "none",
    )
    result.run_summary.update(
        {
            "scenario": run_key.scenario,
            "scenario_name": run_key.scenario,
            "nodes": run_key.node_count,
            "node_count": run_key.node_count,
            "adr": "on" if run_key.adr_enabled else "off",
            "adr_enabled": run_key.adr_enabled,
            "channel_selection": run_key.channel_selection,
        }
    )
    written = write_run_csvs(result, {"root": run_dir, "raw": run_dir / "raw", "per_run": run_dir / "per_run"})
    status_path.write_text(
        json.dumps({"status": "completed", "run_key": run_key.to_dict(), "csv": {k: str(v) for k, v in written.items()}}, indent=2),
        encoding="utf-8",
    )
    _log(layout, "run_completed", run_key=run_key.to_dict(), run_dir=str(run_dir))


def _jamming_windows(scenario: JammingScenario, *, seed: int) -> list[JammingEvent]:
    rng = random.Random(seed)
    windows: list[JammingEvent] = []
    for jammer in scenario.jammers:
        for channel_hz in jammer.channels_hz:
            windows.append(
                JammingEvent(
                    jammer_id=jammer.jammer_id,
                    time_s=rng.uniform(0.0, 10.0),
                    duration_s=1.0,
                    sf=7,
                    frequency_mhz=channel_hz / 1_000_000.0,
                    tx_power_dbm=jammer.tx_power_dbm,
                )
            )
    return windows


def _write_campaign_metadata(layout: CampaignLayout, runs: Sequence[JammingRunKey], *, config: Mapping[str, Any] | None) -> None:
    payload = {"created_at": datetime.now(timezone.utc).isoformat(), "runs": [run.to_dict() for run in runs], **dict(config or {})}
    (layout.root / "config_used.yaml").write_text(yaml.safe_dump(payload, sort_keys=True, allow_unicode=True), encoding="utf-8")
    command = " ".join(shlex.quote(part) for part in sys.argv) if sys.argv else ""
    (layout.root / "commands.txt").write_text(command + "\n", encoding="utf-8")
    _log(layout, "campaign_prepared", runs=len(runs), command=command)


def _log(layout: CampaignLayout, event: str, **payload: Any) -> None:
    layout.logs_dir.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, **payload}
    with (layout.logs_dir / "campaign.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _coerce_layout(layout: CampaignLayout | str | Path | Mapping[str, Any]) -> CampaignLayout:
    if isinstance(layout, CampaignLayout):
        return layout
    if isinstance(layout, Mapping):
        root = layout.get("root", layout.get("base_dir", layout.get("output_dir")))
        if root is None:
            raise ValueError("Le layout mapping doit contenir root, base_dir ou output_dir.")
        return CampaignLayout(Path(root))
    return CampaignLayout(Path(layout))


def _parse_non_negative_int(value: str, label: str) -> int:
    parsed = _parse_int(value, label)
    if parsed < 0:
        raise ValueError(f"{label} doit être >= 0.")
    return parsed


def _parse_positive_int(value: str, label: str) -> int:
    parsed = _parse_int(value, label)
    if parsed <= 0:
        raise ValueError(f"{label} doit être > 0.")
    return parsed


def _parse_int(value: str, label: str) -> int:
    if not value:
        raise ValueError(f"{label} ne doit pas être vide.")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{label} doit être un entier: {value!r}.") from exc


def _safe_token(value: object) -> str:
    text = str(value).strip().lower().replace(" ", "_")
    return "".join(char if char.isalnum() or char in {"_", "-", "."} else "_" for char in text) or "unknown"


__all__ = [
    "CampaignLayout",
    "EXPECTED_RUN_CSVS",
    "JammingCampaign",
    "JammingRunKey",
    "build_campaign",
    "dry_run_plan",
    "expand_adr_modes",
    "expand_run_matrix",
    "is_run_complete",
    "parse_nodes_spec",
    "parse_seed_spec",
    "run_campaign",
]

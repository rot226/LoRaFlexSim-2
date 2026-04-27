"""Presets de campagne pour la CLI ``mobilesfrdth``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

SAFE_TIME_BIN_S = 10.0


@dataclass(frozen=True)
class RunPreset:
    """Définition d'un preset exécutable par ``mobilesfrdth run``."""

    name: str
    description: str
    config_relpath: str
    grid: str
    reps: int | None = None
    seed: int | None = None
    sf_range: tuple[int, int] | None = None
    force_time_bin_s: float | None = None


def _with_safe_time_bin(grid: str, time_bin_s: float) -> str:
    token = "time_bin_s="
    chunks = [chunk.strip() for chunk in grid.split(";") if chunk.strip()]
    if any(chunk.startswith(token) for chunk in chunks):
        return ";".join(chunks)
    chunks.append(f"{token}{time_bin_s:g}")
    return ";".join(chunks)


PRESETS: dict[str, RunPreset] = {
    "paper_core": RunPreset(
        name="paper_core",
        description="Grille principale validée pour les résultats cœur papier.",
        config_relpath="experiments/paper_core.yaml",
        grid=(
            "N=40,60,80,100,120,140,160,180,200;speed=1,3;"
            "mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET,THOMPSON;reps=8;seed_base=1234"
        ),
        force_time_bin_s=SAFE_TIME_BIN_S,
    ),
    "paper_fast": RunPreset(
        name="paper_fast",
        description="Version rapide pour smoke/CI locale avec couverture minimale.",
        config_relpath="experiments/paper_fast.yaml",
        grid="N=80,120;speed=1;mode=SNIR_OFF,SNIR_ON;algo=ADR,UCB;reps=2;seed_base=1234",
        force_time_bin_s=SAFE_TIME_BIN_S,
    ),
    "safe": RunPreset(
        name="safe",
        description="Preset de sécurité qui force un time_bin_s compatible Tc.",
        config_relpath="experiments/paper_fast.yaml",
        grid="N=100;speed=1;mode=SNIR_ON;algo=ADR,UCB;reps=2;seed_base=4321",
        force_time_bin_s=SAFE_TIME_BIN_S,
    ),
}


def list_presets() -> list[RunPreset]:
    return [PRESETS[key] for key in sorted(PRESETS)]


def get_preset(name: str) -> RunPreset:
    key = (name or "").strip()
    if key not in PRESETS:
        available = ", ".join(sorted(PRESETS))
        raise ValueError(f"Preset inconnu '{name}'. Disponibles: {available}.")
    return PRESETS[key]


def resolve_preset_config(project_dir: Path, preset: RunPreset) -> Path:
    return project_dir / preset.config_relpath


def materialize_grid(preset: RunPreset) -> str:
    if preset.force_time_bin_s is None:
        return preset.grid
    return _with_safe_time_bin(preset.grid, preset.force_time_bin_s)


def inject_preset_args(args: Any, *, project_dir: Path) -> None:
    """Injecte config/grille/paramètres depuis ``--preset`` si fourni."""

    preset_name = getattr(args, "preset", None)
    if not preset_name:
        return

    preset = get_preset(preset_name)
    setattr(args, "_preset", preset)

    if getattr(args, "grid", None) in (None, ""):
        args.grid = materialize_grid(preset)
    if getattr(args, "config", None) is None:
        args.config = resolve_preset_config(project_dir, preset)
    if getattr(args, "seed", None) is None and preset.seed is not None:
        args.seed = preset.seed
    if getattr(args, "reps", None) is None and preset.reps is not None:
        args.reps = preset.reps
    if getattr(args, "sf_range", None) is None and preset.sf_range is not None:
        args.sf_range = preset.sf_range

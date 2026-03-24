# LoRaFlexSim-2

LoRaFlexSim-2 is a Python LoRa/LoRaWAN simulator for running campaigns, aggregating results, and visualizing network metrics.

## Recommended public entry path

1. **Primary path**: Panel dashboard.
2. **Scriptable path**: `loraflexsim` CLI.
3. **Technical fallback**: `python -m loraflexsim`.

Legacy names and legacy surfaces (`mobilesfrdth`, `sfrd/`, `src/`, `final/`) are no longer part of the public entry path.

## Quick start (Windows 11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

### Launch the dashboard (recommended)

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

### Use the CLI (for automation)

```powershell
loraflexsim --help
loraflexsim presets --list
loraflexsim run --preset paper_fast --out runs/quickstart
```

### Fallback without a console entrypoint

```powershell
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help
python -m loraflexsim --help
```

## Active vs historical folders

| Area | Status | Usage |
| --- | --- | --- |
| `loraflexsim/` | active | engine, dashboard, public CLI |
| `docs/` | active | user documentation |
| `scripts/` | active | bootstrap and automation |
| `qos_cli/` | specialized | advanced QoS campaigns |
| `docs/archive_or_research/` | historical | migration and research memory |
| `pretest_campagne/` | historical/research | reproductions and comparisons |

## Removals / migration

- `sfrd/`, `src/`, and `final/`: removed from the live surface.
- `mobilesfrdth/`: kept only as an internal migration trace, documented as historical.
- Details: `docs/archive_or_research/migration_legacy_surfaces.md`.

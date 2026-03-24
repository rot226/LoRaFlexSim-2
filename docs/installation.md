# Installation (Windows 11 first)

This guide describes the public installation path for LoRaFlexSim-2.

## What is officially supported today

- **Primary**: Panel dashboard.
- **Supported CLI**: `loraflexsim`.
- **Fallback**: `python -m loraflexsim`.

The `mobilesfrdth`, `sfrd/`, `src/`, and `final/` surfaces are historical and must no longer be used as the standard entry path.

## Recommended installation — Windows 11

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

## Quick verification

```powershell
loraflexsim --help
python -m loraflexsim --help
```

## Launch the dashboard

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

If the browser does not open automatically, copy the URL displayed by Panel.

## Windows 11 fallback (repository wrapper)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help
```

## Migration notes

- Historical folders removed from public usage are tracked in `docs/archive_or_research/migration_legacy_surfaces.md`.
- Research workflows remain documented separately in `docs/archive_or_research/`.

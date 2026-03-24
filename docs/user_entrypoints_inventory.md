# Inventory of user entry points

## Current public entry points

| Entry point | Status | Usage |
| --- | --- | --- |
| `panel serve loraflexsim/launcher/dashboard.py --show` | primary | interactive usage |
| `loraflexsim` | official | command-line campaigns |
| `python -m loraflexsim` | fallback | direct Python execution |
| `scripts/loraflexsim.ps1` | Windows 11 wrapper | local fallback |
| `scripts/loraflexsim.sh` | Linux/macOS wrapper | local fallback |

## Non-public entry points (historical / expert)

| Area | Status |
| --- | --- |
| `python -m loraflexsim.run` | technical/historical |
| `qos_cli/` | specialized |
| `pretest_campagne/` | research |
| `docs/archive_or_research/` | documentation archive |

## Surfaces removed from the public narrative

- `legacy CLI alias` (removed)
- `sfrd/`
- `src/`
- `final/`

Migration traceability: `docs/archive_or_research/migration_legacy_surfaces.md`.

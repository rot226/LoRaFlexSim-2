# Language Migration Status

This checklist tracks the prioritized migration of French-language surfaces to English.

## Status legend
- `todo`: not started
- `in_progress`: currently being migrated
- `done`: migration finished and validated

## Batch backlog (priority order)

| Priority | Batch | Scope | Migration steps (must be completed in order) | Status |
|---|---|---|---|---|
| 1 | Entry docs | `README.md`, `docs/README.md`, `docs/installation.md`, `docs/user_entrypoints_inventory.md` | 1) Translate to English. 2) Run `python scripts/check_english_surface.py`. 3) Confirm no new French strings were introduced. | `todo` |
| 2 | UI/dashboard | `loraflexsim/launcher/dashboard.py` | 1) Translate user-facing strings to English. 2) Run `python scripts/check_english_surface.py`. 3) Confirm no new French strings were introduced. | `todo` |
| 3 | CLI messages and operational scripts | `loraflexsim/run.py`, `scripts/run_offline.sh`, `scripts/windows/run_offline.ps1`, `scripts/bootstrap_*` | 1) Translate messages/comments/help surfaces to English. 2) Run `python scripts/check_english_surface.py`. 3) Confirm no new French strings were introduced. | `todo` |
| 4 | Research/archive zones | `pretest_campagne/**`, `experiments/**`, `docs/archive_or_research/**` | 1) Translate to English. 2) Run `python scripts/check_english_surface.py`. 3) Confirm no new French strings were introduced. | `todo` |

## Folder-level migration checklist

- [ ] `README.md` — `todo`
- [ ] `docs/` — `todo`
- [ ] `loraflexsim/launcher/` — `todo`
- [ ] `loraflexsim/` (CLI surfaces) — `todo`
- [ ] `scripts/` (offline + bootstrap surfaces) — `todo`
- [ ] `pretest_campagne/` — `todo`
- [ ] `experiments/` — `todo`
- [ ] `docs/archive_or_research/` — `todo`

## Validation log

- Baseline executed before migration batches:
  - `python scripts/check_english_surface.py` → fails with existing violations in current repository baseline.
- After each batch, append a new log entry with:
  - date/time,
  - files touched,
  - checker result,
  - explicit statement: "No new French strings introduced".

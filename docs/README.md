# `docs/`

## What is this folder for?

This folder contains the project's active documentation: installation, usage guides, advanced workflows, validation, and a top-level repository reading map.

> Language reminder: active project documentation is maintained in **English** by default.

## When should you use it?

- When discovering the project and looking for the right guide.
- When you need to install the environment on Windows 11 or run a documented workflow.
- When you need reference documentation for a CLI, pipeline, or campaign.

## When should you not use it?

- Do not use it to directly modify the simulation engine or automation scripts.
- Do not stay in `docs/` once you have identified the module or command you need to change.

## Entry points / files to open first

- `docs/installation.md`: installation and local environment.
- `docs/user_guide_cli.md`: standard workflow via `mobilesfrdth`.
- `docs/user_guide_dashboard.md`: legacy dashboard usage.
- `docs/advanced_workflows.md`: advanced, historical, or specialized cases.
- `docs/repository_map.md`: top-level repository reading map.
- `docs/architecture_bandit_sf_decision.md`: short architecture note on where SF UCB1 decision/update logic lives (`simulator.py` vs `qos.py`).

## QA perimeter for English-only migration

To unblock CI quickly while preserving full migration goals, the repository now
uses two explicit QA surfaces in `scripts/check_english_surface.py`:

- **`public_surface` (strict, blocking):** must stay English-only.
  - Current scope: `README.md`, `docs/README.md`, `docs/installation.md`,
    `scripts/check_english_surface.py`.
- **`archive_surface` (temporary controlled tolerance):**
  - Scope focused on legacy/archive trees (for example
    `docs/archive_or_research/**` and `pretest_campagne/*archive*` paths).
  - Violations are still reported to keep visibility, but not blocking by
    default.

## Archive convergence plan

- **Phase 1 — documented temporary exclusion (current default):**
  `archive_surface` is non-blocking and tracked in reports.
- **Phase 2 — progressive translation:**
  reduce `archive_surface` violations incrementally while keeping CI green on
  `public_surface`.
- **Phase 3 — global strict control:**
  enable strict mode (`--strict-global`) so both surfaces become blocking and
  enforce English-only repository-wide.

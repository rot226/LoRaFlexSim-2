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
- `docs/user_guide_cli.md`: standard workflow via `loraflexsim`.
- `docs/user_guide_dashboard.md`: current dashboard usage (`panel serve loraflexsim/launcher/dashboard.py --show`).
- `docs/advanced_workflows.md`: advanced, historical, or specialized cases.
- `docs/repository_map.md`: top-level repository reading map.

## Public command entry points

- Dashboard: `panel serve loraflexsim/launcher/dashboard.py --show`
- Official CLI: `loraflexsim --help`
- Python fallback: `python -m loraflexsim --help`

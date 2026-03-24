# `pretest_campagne/iwcmc_archive/`

## In 30 seconds

| Section | Quick answer |
| --- | --- |
| **What is this folder for?** | Keep legacy `iwcmc_archive` campaigns for reproduction, benchmarking, and archival use. |
| **When should you use it?** | When replaying or reviewing historical `snir_static`, `rl_static`, `rl_mobile`, or MED artifacts. |
| **When should you not use it?** | Do not use it for a new standard campaign or as the project's main entry point. |
| **Main entry point** | Start with archive documentation, then use `run_campaign.*` scripts in the relevant subfolder. |
| **Produced outputs** | Historical outputs in `results/pretest_campagne/iwcmc_archive/` and archive artifacts in each sub-campaign. |
| **Detailed documentation** | `docs/archive_or_research/iwcmc_archive.md` and `docs/archive_or_research/README.md`. |

**Historical documentation** — this folder is preserved for legacy campaigns, reproduction, and result comparison.

## Detailed documentation

### Folder purpose

`pretest_campagne/iwcmc_archive/` is a short entry point to artifacts and documentation for the `iwcmc_archive` domain archive.

### Prerequisites

- **Primary documented OS: Windows 11**.
- **Documented shell: PowerShell**.
- **Execution directory: repository root**.
- **Recommended Python version: 3.11**.
- **Packaging support: Python 3.11 to 3.12**.
- **Recommended standard installation:** `python -m pip install -e . --no-build-isolation` after venv activation.
- **`PYTHONPATH=src` is not required** for the standard workflow; it only applies to explicit offline/fallback workarounds documented elsewhere.

### Minimal scenario

For minimal use, first read archive documentation to identify the campaign and scripts to run.

### Run commands

No single run command is maintained in this README; use `run_campaign.ps1` or `run_campaign.sh` in the relevant subfolder.

### Direct links to detailed docs

- `docs/archive_or_research/iwcmc_archive.md`
- `docs/archive_or_research/README.md`

# `pretest_campagne/scenario_b/`

## In 30 seconds

| Section | Quick answer |
| --- | --- |
| **What is this folder for?** | Group mobility experiments for MNE3SD scenario B. |
| **When should you use it?** | When replaying range, speed, or gateway sweeps for scenario B. |
| **When should you not use it?** | Do not use it for the standard `mobilesfrdth` CLI workflow or another `pretest_campagne` scenario. |
| **Main entry point** | `pretest_campagne.scenario_b.scenarios.run_mobility_*` scripts or `python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_b`. |
| **Produced outputs** | CSV files in `results/mne3sd/scenario_b/` and figures in `figures/mne3sd/scenario_b/`. |
| **Detailed documentation** | This README documents available sweeps, execution profiles, and generation commands. |

## Detailed documentation

### Folder role

This folder contains scripts used to reproduce mobility-focused experiments for MNE3SD scenario B.

### Covered scenarios

- `urban_canyon`
- `rural_highway`
- `industrial_campus`

### Shared simulation parameters

Scenario entrypoints include:

- `--config`
- `--seed`
- `--runs`
- `--duration`
- `--distance-min` / `--distance-max`
- `--speed-min` / `--speed-max`
- `--output` or `--results`

### Execution profiles

Scenario launchers support shared `--profile` and `MNE3SD_PROFILE`:

- `full` *(default)*
- `ci`

### Parallelization

`run_mobility_range_sweep.py`, `run_mobility_speed_sweep.py`, and `run_mobility_gateway_sweep.py` support `--workers`.

### Generate data

```powershell
python -m pretest_campagne.scenario_b.scenarios.run_mobility_range_sweep `
    --replicates 5 --seed 321 `
    --results results/mne3sd/scenario_b/mobility_range_custom.csv
```

### Generate figures

```powershell
python -m pretest_campagne.scenario_b.plots.<figure_module> `
    --input results/mne3sd/scenario_b/<scenario_name>.csv `
    --figures-dir figures/mne3sd/scenario_b/ `
    --format pdf
```

# `pretest_campagne/scenario_d/`

## In 30 seconds

| Section | Quick answer |
| --- | --- |
| **What is this folder for?** | Group mobility experiments for MNE3SD scenario D and D1–D10 variants. |
| **When should you use it?** | When replaying or tuning a scenario D mobility campaign with range, speed, gateway, or load sweeps. |
| **When should you not use it?** | Do not use it for a standard `mobilesfrdth` campaign or other `pretest_campagne` scenarios. |
| **Main entry point** | `pretest_campagne.scenario_d.scenarios.run_mobility_*` scripts or `python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_d`. |
| **Produced outputs** | CSV files in `results/mne3sd/scenario_d/` and figures in `figures/mne3sd/scenario_d/`. |
| **Detailed documentation** | This README summarizes scenarios D1–D10, shared parameters, and generation commands. |

## Detailed documentation

### Folder role

This folder contains scripts used to reproduce mobility-focused experiments for MNE3SD scenario D.

### Scenarios D1–D10

| Scenario | Name | Objective |
| --- | --- | --- |
| D1 | `mobility_range_baseline` | Baseline medium-range mobility. |
| D2 | `mobility_range_stress` | Maximum-range robustness under increased channel noise. |
| D3 | `mobility_speed_baseline` | Impact of nominal speed on PDR. |
| D4 | `mobility_speed_extremes` | Exploration of extreme speeds. |
| D5 | `mobility_gateway_baseline` | Traffic distribution by gateway. |
| D6 | `mobility_gateway_density` | Marginal gain from adding gateways. |
| D7 | `mobility_model_comparison` | Mobility model comparison. |
| D8 | `mobility_interference_load` | Effect of increased radio load. |
| D9 | `mobility_reliability_ci` | Fast set for CI validation. |
| D10 | `mobility_full_campaign` | Full scenario D campaign. |

### Shared simulation parameters

Scripts expose: `--seed`, `--runs`, `--duration`, `--distance-min`, `--distance-max`, `--speed-min`, `--speed-max`, `--output` or `--results`, plus `--profile` and `--workers` depending on the sweep.

### Generate data

```powershell
python -m pretest_campagne.scenario_d.scenarios.run_mobility_range_sweep `
    --replicates 5 --seed 321 `
    --results results/mne3sd/scenario_d/mobility_range_custom.csv
```

### Generate figures

```powershell
python -m pretest_campagne.scenario_d.plots.<figure_module> `
    --input results/mne3sd/scenario_d/<scenario_name>.csv `
    --figures-dir figures/mne3sd/scenario_d/ `
    --format png
```

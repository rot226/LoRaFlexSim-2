# SNIR-Aware Resource Allocation in LoRaWAN with Reinforcement Learning under Mobility

This folder groups artifacts related to the MED section for `pretest_campagne/iwcmc_archive`.

## Structure

- `simulations/`: MED simulation configurations and raw outputs.
- `figures/`: final figures used in the manuscript (MED1 to MED8).
- `scripts/`: scripts for generation, post-processing, and MED figure export.
- `data/`: intermediate datasets used by scripts.

## Scripts (conventions)

Each script in `scripts/` should specify in its header:

- script objective,
- expected inputs (folder or files in `data/` or `simulations/`),
- generated outputs (files written to `figures/`).

Name scripts by main action and target figure, for example:

- `build_med1_traffic_profile.py`
- `plot_med4_snir_cdf.py`

## MED figure naming

Final figures follow `MED<n>.svg`, where `<n>` is a number from 1 to 8.

| File | Expected content |
| --- | --- |
| `MED1.svg` | Mobility profile / scenario (to be specified). |
| `MED2.svg` | Resource allocation vs mobility (to be specified). |
| `MED3.svg` | SNIR vs time / distance (to be specified). |
| `MED4.svg` | SNIR / PDR CDF (to be specified). |
| `MED5.svg` | RL reward vs iterations (to be specified). |
| `MED6.svg` | SF / channel distribution (to be specified). |
| `MED7.svg` | Baseline comparison (to be specified). |
| `MED8.svg` | Parameter sensitivity (to be specified). |

Update the “Expected content” column as soon as final titles are known.

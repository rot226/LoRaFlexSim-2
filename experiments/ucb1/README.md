# UCB1 Experiments

This folder contains scripts to evaluate the UCB1 algorithm (`LoRaSFSelectorUCB1`) integrated in LoRaFlexSim.

## Simulation scripts

Commands can be run from repository root or from `experiments/ucb1`.

- **Density sweep**:
  ```bash
  python experiments/ucb1/run_ucb1_density_sweep.py
  ```
  Exports `experiments/ucb1/ucb1_density_metrics.csv`.

- **Load sweep**:
  ```bash
  python experiments/ucb1/run_ucb1_load_sweep.py
  ```
  Exports `experiments/ucb1/ucb1_load_metrics.csv` and `experiments/ucb1/ucb1_decision_log.csv`.

- **SNIR on/off demo with time windows**:
  ```bash
  python experiments/ucb1/run_snir_window_demo.py
  ```
  Exports `experiments/ucb1/ucb1_snir_window_demo.csv`.

- **UCB1 / ADR / MixRA comparison**:
  ```bash
  python experiments/ucb1/run_baseline_comparison.py
  ```
  Exports `experiments/ucb1/ucb1_baseline_metrics.csv` and `experiments/ucb1/ucb1_baseline_decision_log.csv`.

## Shared CSV columns

- `num_nodes`
- `cluster`
- `sf`
- `reward_mean`
- `der`
- `pdr`
- `snir_avg`
- `success_rate`

## Decision log columns

- `episode_idx`
- `decision_idx`
- `time_s`
- `reward`
- `pdr`
- `throughput`
- `snir_db`
- `sf` / `tx_power`

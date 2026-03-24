# SNIR Experiments — Step 1

## Prerequisites
- Python 3.10 or newer.
- Dependencies installed in editable mode:
  ```bash
  pip install -e .
  ```

## Simulation scripts
Each scenario writes a CSV into `data/` at the repository root.

- Density (PDR/DER/SNIR by cluster):
  ```bash
  python experiments/snir_stage1/scenarios/der_density.py
  # -> data/der_density.csv
  ```
- Load (send-interval variation):
  ```bash
  python experiments/snir_stage1/scenarios/der_load.py
  # -> data/der_load.csv
  ```
- Offered traffic and channel utilization:
  ```bash
  python experiments/snir_stage1/scenarios/offered_traffic.py
  # -> data/offered_traffic.csv
  ```
- Aggregate throughput and collisions:
  ```bash
  python experiments/snir_stage1/scenarios/throughput.py
  # -> data/throughput.csv
  ```

## Figure generation
- PDR/DER versus density:
  ```bash
  python scripts/plot_der_density.py --input data/der_density.csv --output-dir plots/snir_stage1 --pdr-target 0.9
  ```
  PNG and PDF figures are produced in `plots/snir_stage1/`.

## Radio configuration reminders
- Enable `flora_mode=True` to apply FLoRa thresholds and capture behavior.
- Use `snir_model=True` and `interference_model=True` when comparing baseline vs SNIR.
- Provided scenarios already enforce FLoRa non-orthogonality delta (`DEFAULT_NON_ORTH_DELTA`) across channels and flag channels to use SNIR.

## Step 2 preparation (do not run yet)
- Prepare plots for `der_load`, `offered_traffic`, and `throughput` using generated CSV files.
- Prepare an SNIR campaign varying `flora_mode`, `snir_model`, and `interference_model` to measure individual impact.
- Extend documentation with validation methodology and indicators to monitor in the next step.

# Offline Runbook

This guide describes the **exact** commands to run from the repository root in order to
reproduce Step 1 CSV outputs, generate extended figures, and execute
SNIR/QoS tests. No network connection is required.

> **IEEE note**: **IEEE-ready** figures correspond to Step 1 outputs, located
> in `figures/step1/extended/`. Step 2 (comparison) figures are
> not IEEE-ready.

## 1) Step 1 — Generate CSV outputs

```bash
python scripts/run_step1_matrix.py --algos adr apra mixra_h mixra_opt --with-snir true false --seeds 1 2 3 --nodes 1000 5000 --packet-intervals 300 600
python scripts/aggregate_step1_results.py --strict-snir-detection
```

Expected outputs:
- Raw CSV files: `results/step1/<snir_state>/seed_<seed>/`.
- Aggregated CSV files: `results/step1/summary.csv` and `results/step1/raw_index.csv`.

## 2) Step 2 — Comparison and Step 2 figures

```bash
python scripts/run_step2_scenarios.py
python scripts/plot_step1_results.py --official --use-summary --plot-cdf
python scripts/plot_step2_comparison.py
```

Expected outputs:
- Step 2 normalization: `results/step2/raw` and `results/step2/agg`.
- Step 1 figures (IEEE-ready): `figures/step1/extended/`.
- Step 2 figures (comparison): `figures/step2/*.png` and `figures/step2/*.pdf`.

## 3) Run SNIR/QoS tests

> **Fast** tests should include **multiple network sizes**;
> for example, use `--network-sizes 80 160 320 640 1280` to cover
> multiple scales quickly.

### SNIR

```bash
python scripts/validate_snir_plots.py --nodes 8 --duration 120 --packet-interval 60
pytest tests/qos/test_snir_window_effect.py
```

### QoS

```bash
pytest tests/test_qos_clusters.py
pytest tests/test_qos_validation_script.py
```

## Windows PowerShell section

> Run these commands in a PowerShell terminal (Windows 11).

### Safe cleanup of results (Windows)

```powershell
if (Test-Path .\pretest_campagne.scenario_c\step1\results) { Remove-Item -Recurse -Force .\pretest_campagne.scenario_c\step1\results }
if (Test-Path .\pretest_campagne.scenario_c\step2\results) { Remove-Item -Recurse -Force .\pretest_campagne.scenario_c\step2\results }
```

### 1) Step 1 — Generate CSV outputs

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_step1_matrix_windows.ps1
python scripts/aggregate_step1_results.py --strict-snir-detection
```

### 2) Step 2 — Comparison and Step 2 figures

```powershell
python scripts/run_step2_scenarios.py
python scripts/plot_step1_results.py --official --use-summary --plot-cdf
python scripts/plot_step2_comparison.py
```

### 3) Run SNIR/QoS tests

```powershell
python scripts/validate_snir_plots.py --nodes 8 --duration 120 --packet-interval 60
pytest tests/qos/test_snir_window_effect.py
pytest tests/test_qos_clusters.py
pytest tests/test_qos_validation_script.py
```

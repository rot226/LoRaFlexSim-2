#!/usr/bin/env bash
set -euo pipefail

# Orchestrateur de l'archive métier pretest_campagne/iwcmc_archive — variante RL mobile.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_DIR="$REPO_DIR/results/pretest_campagne/iwcmc_archive/rl_mobile"
FIGURES_DIR="$REPO_DIR/figures/pretest_campagne/iwcmc_archive/rl_mobile"
SCENARIO_SCRIPT="$SCRIPT_DIR/scenarios/run_rl_mobile.py"
PLOT_SCRIPT="$SCRIPT_DIR/plots/plot_rlm_figures.py"

mkdir -p "$RESULTS_DIR" "$FIGURES_DIR"
cd "$REPO_DIR"

echo "=== Archive métier pretest_campagne/iwcmc_archive — RL mobile : génération des résultats ==="
python "$SCENARIO_SCRIPT" "$@"

echo "=== Archive métier pretest_campagne/iwcmc_archive — RL mobile : génération des figures ==="
python "$PLOT_SCRIPT"

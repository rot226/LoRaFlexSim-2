#!/usr/bin/env bash
set -euo pipefail

# Orchestrateur de campagne pretest_campagne/iwcmc_archive.


ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

python pretest_campagne/iwcmc_archive/rl_static/scenarios/run_ucb1_vs_qos.py "$@"
python pretest_campagne/iwcmc_archive/rl_static/plots/plot_rls_figures.py

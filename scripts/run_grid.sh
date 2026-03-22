#!/usr/bin/env bash
set -euo pipefail

RUN_ARGS=${1:---help}
AGGREGATE_ARGS=${2:---help}
PLOTS_ARGS=${3:---help}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN=${PYTHON:-python}

cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

run_cmd() {
  local subcommand=$1
  local raw_args=$2
  echo "[mobilesfrdth] ${subcommand} ${raw_args}"
  # Les arguments sont transmis sous forme de chaîne complète pour rester cohérents
  # avec le wrapper PowerShell existant (`run_grid.ps1`).
  eval "\"${PYTHON_BIN}\" -m mobilesfrdth ${subcommand} ${raw_args}"
}

run_cmd run "${RUN_ARGS}"
run_cmd aggregate "${AGGREGATE_ARGS}"
run_cmd plots "${PLOTS_ARGS}"

echo "Pipeline mobilesfrdth terminé (point d'entrée officiel recommandé)."

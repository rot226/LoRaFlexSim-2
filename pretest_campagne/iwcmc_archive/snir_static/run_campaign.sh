#!/usr/bin/env bash
# -------------------------------------------------------------------------------------------------
# Objectif :
#   Orchestrer l'archive métier pretest_campagne/iwcmc_archive — variante SNIR statique (S1–S8),
#   vérifier la présence des CSV générés, puis lancer les scripts de tracé associés.
#
# Paramètres :
#   --python <executable>  Chemin/nom de l'exécutable Python à utiliser (défaut: python).
#   --skip-plots           Ne pas lancer la génération des figures.
#   -h, --help             Afficher l'aide.
#
# Sorties :
#   - results/pretest_campagne/iwcmc_archive/snir_static/S1.csv ... S8.csv
#   - figures/pretest_campagne/iwcmc_archive/snir_static/S1.png/.pdf ... S8.png/.pdf (sauf --skip-plots)
# -------------------------------------------------------------------------------------------------
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./run_campaign.sh [--python <executable>] [--skip-plots]

Options:
  --python <executable>  Chemin/nom de l'exécutable Python à utiliser.
  --skip-plots           Ne pas lancer la génération des figures.
  -h, --help             Afficher l'aide.
USAGE
}

PYTHON_BIN="python"
SKIP_PLOTS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    --skip-plots)
      SKIP_PLOTS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Option inconnue: $1" >&2
      usage
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CAMPAIGN_RESULTS_DIR="$REPO_DIR/results/pretest_campagne/iwcmc_archive"
CAMPAIGN_FIGURES_DIR="$REPO_DIR/figures/pretest_campagne/iwcmc_archive"
DATA_DIR="$CAMPAIGN_RESULTS_DIR/snir_static"
FIGURES_DIR="$CAMPAIGN_FIGURES_DIR/snir_static"

mkdir -p "$DATA_DIR" "$FIGURES_DIR"

SCENARIOS=(S1 S2 S3 S4 S5 S6 S7 S8)

echo "=== Archive métier pretest_campagne/iwcmc_archive — SNIR statique : exécution des scénarios ==="
for scenario in "${SCENARIOS[@]}"; do
  echo "-> ${scenario}"
  "$PYTHON_BIN" "$SCRIPT_DIR/scenarios/${scenario}.py"
done

echo "=== Archive métier pretest_campagne/iwcmc_archive — SNIR statique : vérification des CSV ==="
missing_csv=0
for scenario in "${SCENARIOS[@]}"; do
  csv_path="$DATA_DIR/${scenario}.csv"
  if [[ -f "$csv_path" ]]; then
    echo "OK  : ${csv_path}"
  else
    echo "WARN: ${csv_path} manquant" >&2
    missing_csv=1
  fi
done

if [[ $missing_csv -ne 0 ]]; then
  echo "Attention: certains CSV sont manquants dans $DATA_DIR." >&2
fi

if [[ $SKIP_PLOTS -eq 0 ]]; then
  echo "=== Archive métier pretest_campagne/iwcmc_archive — SNIR statique : génération des figures ==="
  for scenario in "${SCENARIOS[@]}"; do
    echo "-> plot_${scenario}"
    "$PYTHON_BIN" "$SCRIPT_DIR/plots/plot_${scenario}.py"
  done
else
  echo "=== Génération des figures ignorée (--skip-plots) ==="
fi

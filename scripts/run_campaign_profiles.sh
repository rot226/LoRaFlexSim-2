#!/usr/bin/env bash
set -euo pipefail

PROFILE=${1:-core_article}
OUT=${2:-runs/campaign_profiles}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN=${PYTHON:-python}

cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

base_args=(
  run
  --config experiments/default.yaml
  --out "${OUT}"
)

case "${PROFILE}" in
  smoke)
    grid='N=50;speed=1;mode=SNIR_OFF,SNIR_ON;algo=ADR,UCB;reps=1;duration_s=300;seed_base=1234'
    extra=(--max-runs 4 --max-walltime 1200)
    ;;
  core_article)
    grid='N=50,100,160;speed=1,3;mode=SNIR_OFF,SNIR_ON;algo=ADR,MIXRA_H,MIXRA_OPT,UCB;reps=3;duration_s=1800;seed_base=1234'
    extra=(--resume --max-walltime 21600)
    ;;
  full_article)
    grid='N=50,100,160,320;speed=0,1,3,6;mode=SNIR_OFF,SNIR_ON;algo=ADR,MIXRA_H,MIXRA_OPT,UCB;reps=5;duration_s=3600;seed_base=1234'
    extra=(--resume --max-walltime 172800)
    ;;
  *)
    echo "Profil non supporté: ${PROFILE}" >&2
    echo "Profils disponibles: smoke | core_article | full_article" >&2
    exit 1
    ;;
esac

cmd=("${base_args[@]}" --grid "${grid}" "${extra[@]}")

echo "[loraflexsim] Point d'entrée officiel recommandé"
echo "[loraflexsim] Profil=${PROFILE}"
echo "[loraflexsim] Sortie=${OUT}"
echo "[loraflexsim] Commande: ${PYTHON_BIN} -m loraflexsim ${cmd[*]}"

"${PYTHON_BIN}" -m loraflexsim "${cmd[@]}"

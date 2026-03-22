#!/usr/bin/env bash
set -euo pipefail

CONFIG=${CONFIG:-experiments/default.yaml}
OUT_ROOT=${OUT_ROOT:-runs/offline}
GRID=${GRID:-N=50,100;speed=1,3;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET}
REPS=${REPS:-2}
SEED=${SEED:-1234}
SF_RANGE=${SF_RANGE:-7-12}
NO_BONUS=${NO_BONUS:-0}
SCENARIO_FILTERS=()
PYTHON_BIN=${PYTHON:-python}

usage() {
  cat <<'USAGE'
Usage: ./scripts/run_offline.sh [options]

Options:
  --config <path>             Fichier de configuration (défaut: experiments/default.yaml)
  --out-root <path>           Répertoire de sortie racine (défaut: runs/offline)
  --grid <spec>               Grille mobilesfrdth (défaut: N=50,100;speed=1,3;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET)
  --reps <n>                  Nombre de répétitions (défaut: 2)
  --seed <n>                  Graine de base (défaut: 1234)
  --sf-range <range>          Plage de spreading factors (défaut: 7-12)
  --scenario-filter <value>   Filtre de scénario à répéter (option multi-valuée)
  --no-bonus                  Désactive les figures bonus
  --python <executable>       Exécutable Python à utiliser (défaut: python ou $PYTHON)
  -h, --help                  Affiche cette aide
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --out-root)
      OUT_ROOT="$2"
      shift 2
      ;;
    --grid)
      GRID="$2"
      shift 2
      ;;
    --reps)
      REPS="$2"
      shift 2
      ;;
    --seed)
      SEED="$2"
      shift 2
      ;;
    --sf-range)
      SF_RANGE="$2"
      shift 2
      ;;
    --scenario-filter)
      SCENARIO_FILTERS+=("$2")
      shift 2
      ;;
    --no-bonus)
      NO_BONUS=1
      shift
      ;;
    --python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Option inconnue: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

echo "PYTHONPATH=${PYTHONPATH}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python introuvable dans le PATH. Activez votre venv puis relancez ce script." >&2
  exit 1
fi

version_text="$(${PYTHON_BIN} -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ ! "${version_text}" =~ ^3\.(11|12)$ ]]; then
  cat >&2 <<EOF2
Version Python active: ${version_text}
Version non supportée. Ce dépôt reste volontairement sur Python 3.11/3.12.
Contournement offline (Linux/macOS recommandé):
  python3.11 -m venv .venv
  source .venv/bin/activate
  python -m pip install matplotlib PyYAML
  ./scripts/run_offline.sh
EOF2
  exit 2
fi

echo "Version Python active: ${version_text} (supportée)"

missing_modules=()
for module in matplotlib yaml; do
  if ! "${PYTHON_BIN}" -c "import ${module}" >/dev/null 2>&1; then
    missing_modules+=("${module}")
  fi
done

if [[ ${#missing_modules[@]} -gt 0 ]]; then
  echo "Dépendances manquantes: ${missing_modules[*]}" >&2
  echo "Installez les dépendances minimales du flux offline puis relancez: python -m pip install matplotlib PyYAML" >&2
  echo "Alternative complète: python -m pip install -e . --no-build-isolation" >&2
  exit 3
fi

echo "[1/4] run"
"${PYTHON_BIN}" -m mobilesfrdth run --config "${CONFIG}" --out "${OUT_ROOT}" --grid "${GRID}" --reps "${REPS}" --seed "${SEED}" --sf-range "${SF_RANGE}"

aggregates_dir="${OUT_ROOT}/aggregates"
figures_dir="${OUT_ROOT}/figures"

echo "[2/4] aggregate"
"${PYTHON_BIN}" -m mobilesfrdth aggregate --results "${OUT_ROOT}" --out "${aggregates_dir}"

echo "[3/4] plots"
plot_args=(-m mobilesfrdth plots --aggregates-dir "${aggregates_dir}" --out "${figures_dir}")
for filter in "${SCENARIO_FILTERS[@]}"; do
  plot_args+=(--scenario-filter "${filter}")
done
if [[ "${NO_BONUS}" == "1" ]]; then
  plot_args+=(--no-bonus)
fi
"${PYTHON_BIN}" "${plot_args[@]}"

echo "[4/4] validate"
"${PYTHON_BIN}" -m mobilesfrdth.qa.validate_results --aggregates-dir "${aggregates_dir}" --plots-summary "${figures_dir}/plots_summary.json"

echo "Pipeline offline terminé avec succès via le point d’entrée officiel recommandé mobilesfrdth."
echo "Les flux sfrd, final et mobile-sfrd restent réservés aux cas avancés ou historiques."

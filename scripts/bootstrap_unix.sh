#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

choose_python() {
  if command -v python3.11 >/dev/null 2>&1; then
    printf '%s\n' python3.11
    return
  fi
  if command -v python3.12 >/dev/null 2>&1; then
    printf '%s\n' python3.12
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    printf '%s\n' python
    return
  fi
  return 1
}

show_run_command() {
  local editable_installed=$1

  printf '\n==== Commande à utiliser ====\n'
  if [[ "${editable_installed}" == "true" ]]; then
    printf '%s\n' 'Point d\''entrée officiel recommandé installé :' \
      '  mobilesfrdth --help' \
      '  mobilesfrdth presets --list' \
      '  # CLI avancée / spécialisée seulement si besoin identifié :' \
      '  python -m sfrd.cli.run_campaign --help'
  else
    printf '%s\n' 'Mode fallback sans installation editable :' \
      '  ./scripts/mobilesfrdth.sh --help' \
      '  # (équivalent direct)' \
      '  PYTHONPATH=src python -m mobilesfrdth --help'
  fi
}

PYTHON_CMD="$(choose_python)" || {
  echo "Aucun interpréteur Python 3.11/3.12/3 n'a été trouvé dans le PATH." >&2
  exit 1
}

if [[ ! -d .venv ]]; then
  echo "Création de l'environnement virtuel .venv avec ${PYTHON_CMD}..."
  "${PYTHON_CMD}" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Version Python active :"
python --version

echo "Installation du projet en mode editable (sans build isolation)..."
if python -m pip install -e . --no-build-isolation; then
  echo "Bootstrap Unix terminé."
  show_run_command true
  exit 0
fi

echo "Échec de 'pip install -e . --no-build-isolation'." >&2
echo "Basculer en mode fallback PYTHONPATH=src pour conserver mobilesfrdth comme point d'entrée recommandé." >&2
show_run_command false

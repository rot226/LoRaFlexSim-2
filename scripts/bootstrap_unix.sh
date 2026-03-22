#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

is_supported_python() {
  local candidate=$1
  if ! command -v "${candidate}" >/dev/null 2>&1; then
    return 1
  fi

  local version
  version="$("${candidate}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
  [[ "${version}" == "3.11" || "${version}" == "3.12" ]]
}

choose_python() {
  local candidate
  for candidate in python3.11 python3.12 python3 python; do
    if is_supported_python "${candidate}"; then
      printf '%s\n' "${candidate}"
      return
    fi
  done
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
  echo "Aucun interpréteur Python 3.11 ou 3.12 supporté n'a été trouvé dans le PATH." >&2
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

ACTIVE_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "${ACTIVE_VERSION}" != "3.11" && "${ACTIVE_VERSION}" != "3.12" ]]; then
  echo "Version Python non supportée dans .venv : ${ACTIVE_VERSION}. Utiliser Python 3.11 ou 3.12." >&2
  exit 1
fi

echo "Installation du projet en mode editable (sans build isolation)..."
if python -m pip install -e . --no-build-isolation; then
  echo "Bootstrap Unix terminé."
  show_run_command true
  exit 0
fi

echo "Échec de 'pip install -e . --no-build-isolation'." >&2
echo "Basculer en mode fallback PYTHONPATH=src pour conserver mobilesfrdth comme point d'entrée recommandé." >&2
show_run_command false

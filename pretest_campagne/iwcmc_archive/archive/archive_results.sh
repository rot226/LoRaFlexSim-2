#!/usr/bin/env bash
set -euo pipefail

pretest_campagne/iwcmc_archive_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPO_DIR=$(cd "$pretest_campagne/iwcmc_archive_DIR/.." && pwd)
ARCHIVE_DIR="$pretest_campagne/iwcmc_archive_DIR/archive"

mkdir -p "$ARCHIVE_DIR"

stamp=$(date +"%Y%m%d_%H%M%S")
archive_path="$ARCHIVE_DIR/iwcmc_results_${stamp}.tar.gz"

targets=()
for rel in "pretest_campagne/iwcmc_archive/snir_static/data" "figures/pretest_campagne/iwcmc_archive/snir_static" "pretest_campagne/iwcmc_archive/rl_static/figures" "figures/pretest_campagne/iwcmc_archive/rl_mobile" "results/pretest_campagne/iwcmc_archive"; do
  if [ -d "$REPO_DIR/$rel" ]; then
    targets+=("$rel")
  fi
done

if [ ${#targets[@]} -eq 0 ]; then
  echo "Aucun dossier de résultats à archiver." >&2
  exit 1
fi

tar -czf "$archive_path" -C "$REPO_DIR" "${targets[@]}"

echo "Archive créée : $archive_path"

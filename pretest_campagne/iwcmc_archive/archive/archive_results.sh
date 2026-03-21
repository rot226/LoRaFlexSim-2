#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAMPAIGN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$(cd "$CAMPAIGN_DIR/../.." && pwd)"
ARCHIVE_DIR="$CAMPAIGN_DIR/archive"
RESULTS_ROOT="results/pretest_campagne/iwcmc_archive"
FIGURES_ROOT="figures/pretest_campagne/iwcmc_archive"

mkdir -p "$ARCHIVE_DIR"

stamp=$(date +"%Y%m%d_%H%M%S")
archive_path="$ARCHIVE_DIR/pretest_campagne_archive_results_${stamp}.tar.gz"

targets=()
for rel in \
  "$RESULTS_ROOT/snir_static" \
  "$RESULTS_ROOT/rl_static" \
  "$RESULTS_ROOT/rl_mobile" \
  "$FIGURES_ROOT/snir_static" \
  "$FIGURES_ROOT/rl_static" \
  "$FIGURES_ROOT/rl_mobile" \
  "$RESULTS_ROOT"; do
  if [ -d "$REPO_DIR/$rel" ]; then
    targets+=("$rel")
  fi
done

if [ ${#targets[@]} -eq 0 ]; then
  echo "Aucun dossier de résultats ou de figures pretest_campagne à archiver." >&2
  exit 1
fi

tar -czf "$archive_path" -C "$REPO_DIR" "${targets[@]}"

echo "Archive pretest_campagne créée : $archive_path"

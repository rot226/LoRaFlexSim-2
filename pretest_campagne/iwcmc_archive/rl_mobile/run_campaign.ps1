$ErrorActionPreference = "Stop"

# Orchestrateur de campagne pretest_campagne/iwcmc_archive.

$rootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $rootDir

python pretest_campagne/iwcmc_archive/rl_mobile/scenarios/run_rl_mobile.py @Args
python pretest_campagne/iwcmc_archive/rl_mobile/plots/plot_rlm_figures.py

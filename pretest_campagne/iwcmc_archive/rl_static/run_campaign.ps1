$ErrorActionPreference = "Stop"

# Orchestrateur de campagne pretest_campagne/iwcmc_archive.

$rootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $rootDir

python pretest_campagne/iwcmc_archive/rl_static/scenarios/run_ucb1_vs_qos.py @Args
python pretest_campagne/iwcmc_archive/rl_static/plots/plot_rls_figures.py

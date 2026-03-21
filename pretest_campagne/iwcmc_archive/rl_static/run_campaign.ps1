$ErrorActionPreference = "Stop"

# Orchestrateur de l'archive métier pretest_campagne/iwcmc_archive — variante RL statique.

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot ".." ".." "..")
$ResultsRoot = Join-Path (Join-Path $RepoRoot "results") "pretest_campagne"
$FiguresRoot = Join-Path (Join-Path $RepoRoot "figures") "pretest_campagne"
$CampaignResultsDir = Join-Path $ResultsRoot "iwcmc_archive"
$CampaignFiguresDir = Join-Path $FiguresRoot "iwcmc_archive"
$ResultsDir = Join-Path $CampaignResultsDir "rl_static"
$FiguresDir = Join-Path $CampaignFiguresDir "rl_static"
$ScenarioScript = Join-Path (Join-Path $PSScriptRoot "scenarios") "run_ucb1_vs_qos.py"
$PlotScript = Join-Path (Join-Path $PSScriptRoot "plots") "plot_rls_figures.py"

New-Item -ItemType Directory -Force -Path $ResultsDir, $FiguresDir | Out-Null
Set-Location $RepoRoot

Write-Host "=== Archive métier pretest_campagne/iwcmc_archive — RL statique : génération des résultats ==="
& python $ScenarioScript @Args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "=== Archive métier pretest_campagne/iwcmc_archive — RL statique : génération des figures ==="
& python $PlotScript
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

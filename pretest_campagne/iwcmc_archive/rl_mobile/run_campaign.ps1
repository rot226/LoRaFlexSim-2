$ErrorActionPreference = "Stop"

# Orchestrateur de l'archive métier pretest_campagne/iwcmc_archive — variante RL mobile.

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot ".." ".." "..")
$ResultsRoot = Join-Path (Join-Path $RepoRoot "results") "pretest_campagne"
$FiguresRoot = Join-Path (Join-Path $RepoRoot "figures") "pretest_campagne"
$CampaignResultsDir = Join-Path $ResultsRoot "iwcmc_archive"
$CampaignFiguresDir = Join-Path $FiguresRoot "iwcmc_archive"
$ResultsDir = Join-Path $CampaignResultsDir "rl_mobile"
$FiguresDir = Join-Path $CampaignFiguresDir "rl_mobile"
$ScenarioScript = Join-Path (Join-Path $PSScriptRoot "scenarios") "run_rl_mobile.py"
$PlotScript = Join-Path (Join-Path $PSScriptRoot "plots") "plot_rlm_figures.py"

New-Item -ItemType Directory -Force -Path $ResultsDir, $FiguresDir | Out-Null
Set-Location $RepoRoot

Write-Host "=== Archive métier pretest_campagne/iwcmc_archive — RL mobile : génération des résultats ==="
& python $ScenarioScript @Args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "=== Archive métier pretest_campagne/iwcmc_archive — RL mobile : génération des figures ==="
& python $PlotScript
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

<#
---------------------------------------------------------------------------------------------------
Objectif :
  Orchestrer l'archive métier pretest_campagne/iwcmc_archive — variante SNIR statique (S1–S8),
  vérifier la présence des CSV générés, puis lancer les scripts de tracé associés.

Paramètres :
  -Python <string>   Chemin/nom de l'exécutable Python à utiliser (défaut: "python").
  -SkipPlots         Ne pas lancer la génération des figures.

Sorties :
  - results/pretest_campagne/iwcmc_archive/snir_static/S1.csv ... S8.csv
  - figures/pretest_campagne/iwcmc_archive/snir_static/S1.png/.pdf ... S8.png/.pdf (sauf -SkipPlots)
---------------------------------------------------------------------------------------------------
#>
[CmdletBinding()]
param(
    [string]$Python = "python",
    [switch]$SkipPlots
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptDir))
$ResultsRoot = Join-Path (Join-Path $RepoRoot "results") "pretest_campagne"
$FiguresRoot = Join-Path (Join-Path $RepoRoot "figures") "pretest_campagne"
$CampaignResultsDir = Join-Path $ResultsRoot "iwcmc_archive"
$CampaignFiguresDir = Join-Path $FiguresRoot "iwcmc_archive"
$DataDir = Join-Path $CampaignResultsDir "snir_static"
$FiguresDir = Join-Path $CampaignFiguresDir "snir_static"
$ScenariosDir = Join-Path $ScriptDir "scenarios"
$PlotsDir = Join-Path $ScriptDir "plots"

New-Item -ItemType Directory -Force -Path $DataDir, $FiguresDir | Out-Null

$scenarios = @("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")

Write-Host "=== Archive métier pretest_campagne/iwcmc_archive — SNIR statique : exécution des scénarios ==="
foreach ($scenario in $scenarios) {
    Write-Host "-> $scenario"
    & $Python (Join-Path $ScenariosDir "$scenario.py")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "=== Archive métier pretest_campagne/iwcmc_archive — SNIR statique : vérification des CSV ==="
$missingCsv = $false
foreach ($scenario in $scenarios) {
    $csvPath = Join-Path $DataDir "$scenario.csv"
    if (Test-Path $csvPath) {
        Write-Host "OK  : $csvPath"
    } else {
        Write-Warning "$csvPath manquant"
        $missingCsv = $true
    }
}

if ($missingCsv) {
    Write-Warning "Attention: certains CSV sont manquants dans $DataDir."
}

if (-not $SkipPlots) {
    Write-Host "=== Archive métier pretest_campagne/iwcmc_archive — SNIR statique : génération des figures ==="
    foreach ($scenario in $scenarios) {
        Write-Host "-> plot_$scenario"
        & $Python (Join-Path $PlotsDir "plot_$scenario.py")
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
} else {
    Write-Host "=== Génération des figures ignorée (-SkipPlots) ==="
}

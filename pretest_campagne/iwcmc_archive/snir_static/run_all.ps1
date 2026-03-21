<#
---------------------------------------------------------------------------------------------------
Objectif :
  Enchaîner les scénarios pretest_campagne/iwcmc_archive SNIR statique (S1–S8), vérifier la présence
  des CSV générés, puis lancer les scripts de tracé associés.

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
$DataDir = Join-Path $RepoRoot "results/pretest_campagne/iwcmc_archive/snir_static"
$FiguresDir = Join-Path $RepoRoot "figures/pretest_campagne/iwcmc_archive/snir_static"

New-Item -ItemType Directory -Force -Path $DataDir, $FiguresDir | Out-Null

$scenarios = @("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")

Write-Host "=== pretest_campagne/iwcmc_archive SNIR statique : exécution des scénarios ==="
foreach ($scenario in $scenarios) {
    Write-Host "-> $scenario"
    & $Python (Join-Path $ScriptDir "scenarios" "$scenario.py")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "=== pretest_campagne/iwcmc_archive SNIR statique : collecte des CSV ==="
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
    Write-Warning "Attention: certains CSV sont manquants."
}

if (-not $SkipPlots) {
    Write-Host "=== pretest_campagne/iwcmc_archive SNIR statique : génération des figures ==="
    foreach ($scenario in $scenarios) {
        Write-Host "-> plot_$scenario"
        & $Python (Join-Path $ScriptDir "plots" "plot_$scenario.py")
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
} else {
    Write-Host "=== Génération des figures ignorée (-SkipPlots) ==="
}

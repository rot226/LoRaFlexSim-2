[CmdletBinding()]
param(
    [string]$Config = "experiments/default.yaml",
    [string]$OutRoot = "runs/offline",
    [string]$Grid = "N=50,100;speed=1,3;mode=SNIR_OFF,SNIR_ON;algo=ADR,ADR_MIXRA,UCB,UCB_FORGET",
    [int]$Reps = 2,
    [int]$Seed = 1234,
    [string]$SfRange = "7-12",
    [string[]]$ScenarioFilter = @(),
    [switch]$NoBonus
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "../..")
Set-Location $repoRoot

$env:PYTHONPATH = $repoRoot.Path
Write-Host "PYTHONPATH=$($env:PYTHONPATH)" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python introuvable dans le PATH. Activez votre venv puis relancez ce script."
    exit 1
}

$versionProbe = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Impossible de lire la version Python active."
    exit 1
}

$versionText = ($versionProbe | Select-Object -First 1).Trim()
$parts = $versionText.Split('.')
$major = [int]$parts[0]
$minor = [int]$parts[1]
if ($major -ne 3 -or $minor -lt 11 -or $minor -gt 12) {
    Write-Host "Version Python active: $versionText" -ForegroundColor Yellow
    Write-Error @"
Version non supportée. Ce dépôt reste volontairement sur Python 3.11/3.12.
Contournement offline (Windows 11 recommandé):
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  powershell -ExecutionPolicy Bypass -File scripts/windows/run_offline.ps1
"@
    exit 2
}

Write-Host "Version Python active: $versionText (supportée)" -ForegroundColor Green

$requiredModules = @("matplotlib", "yaml")
$missing = @()
foreach ($module in $requiredModules) {
    python -c "import $module" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $missing += $module
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Dépendances manquantes: $($missing -join ', ')" -ForegroundColor Yellow
    Write-Error "Installez les dépendances minimales du flux offline puis relancez: python -m pip install matplotlib PyYAML`nAlternative complète: python -m pip install -e . --no-build-isolation"
    exit 3
}

Write-Host "[1/4] run" -ForegroundColor Cyan
python -m mobilesfrdth run --config $Config --out $OutRoot --grid $Grid --reps $Reps --seed $Seed --sf-range $SfRange
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$aggregatesDir = Join-Path $OutRoot "aggregates"
$figuresDir = Join-Path $OutRoot "figures"

Write-Host "[2/4] aggregate" -ForegroundColor Cyan
python -m mobilesfrdth aggregate --results $OutRoot --out $aggregatesDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/4] plots" -ForegroundColor Cyan
$plotArgs = @("-m", "mobilesfrdth", "plots", "--aggregates-dir", $aggregatesDir, "--out", $figuresDir)
foreach ($filter in $ScenarioFilter) {
    $plotArgs += @("--scenario-filter", $filter)
}
if ($NoBonus) {
    $plotArgs += "--no-bonus"
}
python @plotArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/4] validate" -ForegroundColor Cyan
python -m mobilesfrdth.qa.validate_results --aggregates-dir $aggregatesDir --plots-summary (Join-Path $figuresDir "plots_summary.json")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Pipeline offline terminé avec succès via le point d’entrée officiel recommandé `loraflexsim` (backend `mobilesfrdth`)." -ForegroundColor Green
Write-Host "Les workflows de recherche vivent dans `pretest_campagne/` et les pipelines retirés sont documentés sous `docs/archive_or_research/`." -ForegroundColor DarkYellow

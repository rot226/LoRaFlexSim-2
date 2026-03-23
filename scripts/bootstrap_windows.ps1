[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Path
$rootDir = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $rootDir

$venvDir = Join-Path $rootDir ".venv"
$venvPython = Join-Path $venvDir "Scripts/python.exe"
$activateScript = Join-Path $venvDir "Scripts/Activate.ps1"

function Show-RunCommand {
    param(
        [bool]$EditableInstalled
    )

    Write-Host ""
    Write-Host "==== Commande à utiliser ====" -ForegroundColor Cyan

    if ($EditableInstalled) {
        Write-Host "Point d'entrée officiel recommandé installé :" -ForegroundColor Green
        Write-Host "  loraflexsim --help"
        Write-Host "  loraflexsim presets --list"
        Write-Host "  python -m loraflexsim --help"
    } else {
        Write-Host "Mode fallback sans installation editable :" -ForegroundColor Yellow
        Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help"
        Write-Host "  # (équivalent direct)"
        Write-Host "  `$env:PYTHONPATH='.'; python -m loraflexsim --help"
    }
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Error "Le lanceur Python 'py' est introuvable. Installez Python 3.11 ou 3.12 puis relancez ce script."
    exit 1
}

$selectedPython = $null
foreach ($candidate in @('-3.11', '-3.12')) {
    py $candidate -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $selectedPython = $candidate
        break
    }
}

if ($null -eq $selectedPython) {
    Write-Error "Aucune installation Python 3.11 ou 3.12 n'a été détectée via 'py'."
    exit 1
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Création de l'environnement virtuel .venv avec py $selectedPython..."
    py $selectedPython -m venv .venv
}

if (-not (Test-Path $activateScript)) {
    Write-Error "Environnement virtuel introuvable ou incomplet : '$venvDir'. Vérifiez la création de .venv puis relancez ce script."
    exit 1
}

Write-Host "Activation de .venv..."
. $activateScript

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python n'est pas accessible après activation de .venv. Vérifiez '$venvDir'."
    exit 1
}

Write-Host "Version Python active :" -ForegroundColor Cyan
python --version

$activeVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Impossible de lire la version Python active dans .venv."
    exit 1
}
$activeVersion = ($activeVersion | Select-Object -First 1).Trim()
if ($activeVersion -notin @('3.11', '3.12')) {
    Write-Error "Version Python non supportée dans .venv : $activeVersion. Utilisez Python 3.11 ou 3.12."
    exit 1
}

Write-Host "Vérification de l'import setuptools..." -ForegroundColor Cyan
$setuptoolsOk = $true
python -c "import setuptools" 2>$null
if ($LASTEXITCODE -ne 0) {
    $setuptoolsOk = $false
}

if (-not $setuptoolsOk) {
    Write-Warning "Import setuptools KO. Tentative d'installation de setuptools..."
    python -m pip install setuptools
    python -c "import setuptools"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "setuptools reste indisponible : passage en mode fallback via loraflexsim."
        Show-RunCommand -EditableInstalled $false
        exit 0
    }
}

Write-Host "Installation du projet en mode editable (sans build isolation)..." -ForegroundColor Cyan
python -m pip install -e . --no-build-isolation
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Échec de 'pip install -e . --no-build-isolation'."
    Write-Warning "Basculer automatiquement en mode fallback dépôt pour conserver loraflexsim comme point d'entrée recommandé."
    Show-RunCommand -EditableInstalled $false
    exit 0
}

Write-Host "Bootstrap Windows terminé." -ForegroundColor Green
Show-RunCommand -EditableInstalled $true

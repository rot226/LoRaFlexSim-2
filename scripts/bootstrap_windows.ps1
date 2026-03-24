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
    Write-Host "==== Command to use ====" -ForegroundColor Cyan

    if ($EditableInstalled) {
        Write-Host "Recommended official entry point installed:" -ForegroundColor Green
        Write-Host "  loraflexsim --help"
        Write-Host "  loraflexsim presets --list"
        Write-Host "  python -m loraflexsim --help"
    } else {
        Write-Host "Fallback mode without editable install:" -ForegroundColor Yellow
        Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help"
        Write-Host "  # (direct equivalent)"
        Write-Host "  `$env:PYTHONPATH='.'; python -m loraflexsim --help"
    }
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Error "Python launcher 'py' was not found. Install Python 3.11 or 3.12 and rerun this script."
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
    Write-Error "No Python 3.11 or 3.12 installation was detected via 'py'."
    exit 1
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating .venv virtual environment with py $selectedPython..."
    py $selectedPython -m venv .venv
}

if (-not (Test-Path $activateScript)) {
    Write-Error "Virtual environment not found or incomplete: '$venvDir'. Check .venv creation and rerun this script."
    exit 1
}

Write-Host "Activating .venv..."
. $activateScript

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not accessible after activating .venv. Check '$venvDir'."
    exit 1
}

Write-Host "Active Python version:" -ForegroundColor Cyan
python --version

$activeVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Unable to read active Python version in .venv."
    exit 1
}
$activeVersion = ($activeVersion | Select-Object -First 1).Trim()
if ($activeVersion -notin @('3.11', '3.12')) {
    Write-Error "Unsupported Python version in .venv: $activeVersion. Use Python 3.11 or 3.12."
    exit 1
}

Write-Host "Checking setuptools import..." -ForegroundColor Cyan
$setuptoolsOk = $true
python -c "import setuptools" 2>$null
if ($LASTEXITCODE -ne 0) {
    $setuptoolsOk = $false
}

if (-not $setuptoolsOk) {
    Write-Warning "setuptools import failed. Trying to install setuptools..."
    python -m pip install setuptools
    python -c "import setuptools"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "setuptools is still unavailable: switching to fallback mode via loraflexsim."
        Show-RunCommand -EditableInstalled $false
        exit 0
    }
}

Write-Host "Installing project in editable mode (without build isolation)..." -ForegroundColor Cyan
python -m pip install -e . --no-build-isolation
if ($LASTEXITCODE -ne 0) {
    Write-Warning "'pip install -e . --no-build-isolation' failed."
    Write-Warning "Automatically switching to repository fallback mode to keep loraflexsim as recommended entry point."
    Show-RunCommand -EditableInstalled $false
    exit 0
}

Write-Host "Windows bootstrap completed." -ForegroundColor Green
Show-RunCommand -EditableInstalled $true

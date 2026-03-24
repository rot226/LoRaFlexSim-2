<#
Exécution guidée de la matrice d'essais Step 1 sous Windows.

Ce script :
- se place à la racine du dépôt ;
- utilise explicitement le Python du venv local (``.\\venv`` prioritaire, sinon ``.\\env``) ;
- lance ``scripts/run_step1_matrix.py`` avec les paramètres
  recommandés pour générer les CSV sous ``results/step1/<snir_state>/seed_<seed>/``.
#>

[CmdletBinding()]
param(
    [string]$VenvPath = ""
)

$ErrorActionPreference = "Stop"

# Localise la racine du dépôt depuis le dossier scripts/
$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Path
$rootDir = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $rootDir

if ([string]::IsNullOrWhiteSpace($VenvPath)) {
    if (Test-Path ".\\.venv\\Scripts\\python.exe") {
        $VenvPath = ".\\.venv"
    } elseif (Test-Path ".\\env\\Scripts\\python.exe") {
        $VenvPath = ".\\env"
    } else {
        Write-Error "No venv detected. Create one with 'python -m venv .venv' (or 'python -m venv env'), then rerun this script, or provide -VenvPath."
        exit 1
    }
}

$Py = Join-Path $VenvPath "Scripts/python.exe"
if (-not (Test-Path $Py)) {
    Write-Error "Python interpreter not found in venv: $Py"
    exit 1
}

$arguments = @(
    "scripts/run_step1_matrix.py"
    "--algos" "adr" "apra" "mixra_h" "mixra_opt"
    "--with-snir" "true" "false"
    "--seeds" "1" "2" "3"
    "--nodes" "1000" "5000"
    "--packet-intervals" "300" "600"
)

Write-Host "Starting Step 1 matrix with venv Python: $Py"
& $Py @arguments

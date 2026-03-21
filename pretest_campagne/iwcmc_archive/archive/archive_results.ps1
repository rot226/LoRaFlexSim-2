param(
    [string]$RepoRoot = $(Resolve-Path (Join-Path $PSScriptRoot ".." ".."))
)

$iwcmcDir = Join-Path $RepoRoot "pretest_campagne/iwcmc_archive"
$archiveDir = Join-Path $iwcmcDir "archive"
New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archivePath = Join-Path $archiveDir "iwcmc_results_$stamp.tar.gz"

$targets = @(
    "pretest_campagne/iwcmc_archive/snir_static/data",
    "figures/pretest_campagne/iwcmc_archive/snir_static",
    "pretest_campagne/iwcmc_archive/rl_static/figures",
    "figures/pretest_campagne/iwcmc_archive/rl_mobile",
    "results/pretest_campagne/iwcmc_archive"
) | Where-Object { Test-Path (Join-Path $RepoRoot $_) }

if ($targets.Count -eq 0) {
    Write-Error "Aucun dossier de résultats à archiver."
    exit 1
}

$targetArgs = $targets -join " "
Push-Location $RepoRoot
try {
    tar -czf $archivePath $targetArgs
} finally {
    Pop-Location
}

Write-Host "Archive créée : $archivePath"

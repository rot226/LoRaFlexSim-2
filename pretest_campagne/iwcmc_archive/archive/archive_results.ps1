param(
    [string]$RepoRoot = $(Resolve-Path (Join-Path $PSScriptRoot ".." ".." ".."))
)

$CampaignRoot = Join-Path (Join-Path $RepoRoot "pretest_campagne") "iwcmc_archive"
$ArchiveDir = Join-Path $CampaignRoot "archive"
$ResultsRoot = Join-Path (Join-Path (Join-Path $RepoRoot "results") "pretest_campagne") "iwcmc_archive"
$FiguresRoot = Join-Path (Join-Path (Join-Path $RepoRoot "figures") "pretest_campagne") "iwcmc_archive"
New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchivePath = Join-Path $ArchiveDir "pretest_campagne_archive_results_$stamp.tar.gz"

$targets = @(
    (Join-Path $ResultsRoot "snir_static"),
    (Join-Path $ResultsRoot "rl_static"),
    (Join-Path $ResultsRoot "rl_mobile"),
    (Join-Path $FiguresRoot "snir_static"),
    (Join-Path $FiguresRoot "rl_static"),
    (Join-Path $FiguresRoot "rl_mobile"),
    $ResultsRoot
) | Where-Object { Test-Path $_ } | ForEach-Object {
    [System.IO.Path]::GetRelativePath($RepoRoot, $_)
}

if ($targets.Count -eq 0) {
    Write-Error "Aucun dossier de résultats ou de figures pretest_campagne à archiver."
    exit 1
}

Push-Location $RepoRoot
try {
    tar -czf $ArchivePath @targets
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}

Write-Host "Archive pretest_campagne créée : $ArchivePath"

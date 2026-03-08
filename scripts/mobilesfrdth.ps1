$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = (Resolve-Path (Join-Path $repoRoot 'src')).Path

python -m mobilesfrdth @args
exit $LASTEXITCODE

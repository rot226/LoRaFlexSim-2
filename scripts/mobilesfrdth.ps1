$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
# Source canonique unique du package Python `mobilesfrdth`.
$env:PYTHONPATH = (Resolve-Path (Join-Path $repoRoot 'src')).Path

python -m mobilesfrdth @args
exit $LASTEXITCODE

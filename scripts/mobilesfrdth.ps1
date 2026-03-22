$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
# Wrapper fallback Windows pour conserver `mobilesfrdth` comme point d’entrée officiel recommandé.
# Les workflows `sfrd`, `final` et `mobile-sfrd` restent spécialisés ou historiques.
$env:PYTHONPATH = (Resolve-Path (Join-Path $repoRoot 'src')).Path

python -m mobilesfrdth @args
exit $LASTEXITCODE

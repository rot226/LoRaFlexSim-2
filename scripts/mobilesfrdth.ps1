$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
# Wrapper fallback Windows pour conserver `mobilesfrdth` comme alias de compatibilité.
# Le point d’entrée officiel recommandé côté utilisateur est `loraflexsim`.
$env:PYTHONPATH = (Resolve-Path $repoRoot).Path

python -m mobilesfrdth @args
exit $LASTEXITCODE

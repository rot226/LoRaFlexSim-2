$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$resolvedRoot = (Resolve-Path $repoRoot).Path
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$resolvedRoot;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $resolvedRoot
}

python -m loraflexsim @args
exit $LASTEXITCODE

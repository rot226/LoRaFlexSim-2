param(
    [string]$RunArgs = "--help",
    [string]$AggregateArgs = "--help",
    [string]$PlotsArgs = "--help"
)

$ErrorActionPreference = 'Stop'

Write-Host "[1/3] loraflexsim run $RunArgs"
Invoke-Expression "python -m loraflexsim run $RunArgs"

Write-Host "[2/3] loraflexsim aggregate $AggregateArgs"
Invoke-Expression "python -m loraflexsim aggregate $AggregateArgs"

Write-Host "[3/3] loraflexsim plots $PlotsArgs"
Invoke-Expression "python -m loraflexsim plots $PlotsArgs"

Write-Host "loraflexsim pipeline finished (recommended official entry point)."

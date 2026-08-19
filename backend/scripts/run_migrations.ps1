#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run Django migrations with an optional DATABASE_URL.
.DESCRIPTION
    Sets DATABASE_URL into the environment for the current process,
    then runs `python manage.py migrate`.
.PARAMETER DatabaseUrl
    The full DATABASE_URL to use (e.g. postgres://user:pass@host/db).
    When omitted, the script falls back to whatever is already set in the environment.
.EXAMPLE
    pwsh .\run_migrations.ps1 -DatabaseUrl "postgres://user:pass@localhost:5432/teachsense"
#>
param(
    [Parameter(Mandatory = $false)]
    [string]$DatabaseUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$managePy = Join-Path $backendDir 'manage.py'

if (-not (Test-Path -LiteralPath $managePy)) {
    Write-Error "Cannot find manage.py at '$managePy'. Run this script from the backend directory."
    exit 1
}

if ($DatabaseUrl) {
    $env:DATABASE_URL = $DatabaseUrl
}

$current = if ($env:DATABASE_URL) {
    $env:DATABASE_URL
} else {
    "(not set; using project default)"
}
Write-Host "Using DATABASE_URL: $current"

Push-Location -LiteralPath $backendDir
try {
    python manage.py migrate
}
finally {
    Pop-Location
}

exit $LASTEXITCODE

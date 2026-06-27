# Start the local wallet API for desktop dev (127.0.0.1 only)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Error "Run setup.bat first to create the virtual environment."
    exit 1
}

$env:STRICT_SECRETS = "true"
& .\venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8002

# Wallet Vault — start API + Svelte UI (PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$ApiPort = 8001

function Test-PortInUse($Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $conn
}

function Test-ApiHealthy {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/api/health" -TimeoutSec 2
        return $r.status -eq "ok"
    } catch {
        return $false
    }
}

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Error "Run setup.bat first to create the virtual environment."
    exit 1
}

$apiRunning = Test-PortInUse $ApiPort
$uiRunning = Test-PortInUse 5173

if ($apiRunning -and (Test-ApiHealthy)) {
    Write-Host "API already running on http://127.0.0.1:$ApiPort" -ForegroundColor Yellow
} elseif ($apiRunning) {
    Write-Host "Port $ApiPort is in use but API is not responding." -ForegroundColor Red
    Write-Host "Run .\stop_admin.ps1 or close the other process, then try again."
    exit 1
} else {
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$PSScriptRoot'; .\venv\Scripts\uvicorn api.main:app --reload --port $ApiPort"
    ) -WindowStyle Normal
    Write-Host "Started API on http://127.0.0.1:$ApiPort" -ForegroundColor Green
}

if ($uiRunning) {
    Write-Host "Admin UI already running on http://localhost:5173" -ForegroundColor Yellow
} else {
    if (-not (Test-Path "admin\node_modules")) {
        Write-Host "Installing admin UI dependencies..."
        Push-Location admin
        npm install
        Pop-Location
    }

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$PSScriptRoot\admin'; npm run dev"
    ) -WindowStyle Normal
    Write-Host "Started Admin UI on http://localhost:5173" -ForegroundColor Green
}

Write-Host ""
Write-Host "Open: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Login: admin / (password from .env)" -ForegroundColor Cyan
Write-Host "Stop: .\stop_admin.ps1 or close the service windows"

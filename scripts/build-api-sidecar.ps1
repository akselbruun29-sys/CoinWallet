# Build frozen Python API sidecar for Tauri externalBin (Windows x64).
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$Python = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "Run setup.bat first (venv required to build the sidecar)."
}

Write-Host "Building frozen API sidecar (PyInstaller)..." -ForegroundColor Cyan
& $Python -m pip install --quiet pyinstaller
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m PyInstaller (Join-Path $PSScriptRoot "coinwallet-api.spec") --noconfirm --clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Built = Join-Path $Root "dist\coinwallet-api.exe"
if (-not (Test-Path $Built)) {
    Write-Error "PyInstaller output not found: $Built"
}

$BinDir = Join-Path $Root "src-tauri\bin"
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
$Dest = Join-Path $BinDir "coinwallet-api-x86_64-pc-windows-msvc.exe"
Copy-Item $Built $Dest -Force
Write-Host "Staged sidecar at $Dest" -ForegroundColor Green

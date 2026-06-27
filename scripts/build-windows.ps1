# Build CoinWallet for Windows — admin UI + Tauri + copy to releases/
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "Building CoinWallet for Windows..." -ForegroundColor Cyan

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Error "Run setup.bat first."
}

if (-not (Test-Path "admin\node_modules")) {
    Push-Location admin
    npm install
    Pop-Location
}

Write-Host "Pre-release security checks..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "..\venv\Scripts\python.exe") (Join-Path $PSScriptRoot "verify_release_security.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Building admin UI (desktop)..." -ForegroundColor Cyan
npm run build:desktop --prefix admin

Write-Host "Building Tauri bundle..." -ForegroundColor Cyan
cargo tauri build

$exe = Join-Path $PWD "src-tauri\target\release\coinwallet.exe"
if (-not (Test-Path $exe)) {
    Write-Error "Expected binary not found: $exe"
}

$dest = Join-Path $PWD "releases\coinwallet-windows-x64.exe"
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
Copy-Item $exe $dest -Force
Write-Host "Copied to $dest" -ForegroundColor Green

& (Join-Path $PSScriptRoot "sign-release-windows.ps1") -FilePath $dest

$version = (Get-Content "src-tauri\tauri.conf.json" -Raw | ConvertFrom-Json).version
& (Join-Path $PSScriptRoot "update-releases-manifest.ps1") -Version $version -MarkAvailable

& (Join-Path $PSScriptRoot "finalize-release.ps1") -Version $version

Write-Host "Done. Run the installer from src-tauri\target\release\bundle\ if needed." -ForegroundColor Green

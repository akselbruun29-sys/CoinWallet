# Build CoinWallet for Windows - admin UI + Tauri + copy to releases/
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

Write-Host "Staging Tor Expert Bundle (optional - requires network)..." -ForegroundColor Cyan
try {
    & (Join-Path $PSScriptRoot "setup-tor.ps1")
} catch {
    Write-Warning "Tor staging skipped: $_"
}

Write-Host "Building admin UI (desktop)..." -ForegroundColor Cyan
npm run build:desktop --prefix admin
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Building frozen API sidecar..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "build-api-sidecar.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Building Tauri bundle..." -ForegroundColor Cyan
node (Join-Path $PSScriptRoot "patch-tauri-tor-resources.mjs")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
cargo tauri build

$nsisDir = Join-Path $PWD "src-tauri\target\release\bundle\nsis"
$setup = Get-ChildItem -Path $nsisDir -Filter "*-setup.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $setup) {
    Write-Error "NSIS installer not found under $nsisDir - expected *-setup.exe from cargo tauri build"
}

$dest = Join-Path $PWD "releases\coinwallet-windows-x64-setup.exe"
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
Copy-Item $setup.FullName $dest -Force
Write-Host "Copied installer to $dest" -ForegroundColor Green

& (Join-Path $PSScriptRoot "sign-release-windows.ps1") -FilePath $dest

$version = (Get-Content "src-tauri\tauri.conf.json" -Raw | ConvertFrom-Json).version
& (Join-Path $PSScriptRoot "update-releases-manifest.ps1") -Version $version -MarkAvailable

& (Join-Path $PSScriptRoot "finalize-release.ps1") -Version $version

Write-Host "Done. Installed app is listed in Start Menu as CoinWallet." -ForegroundColor Green

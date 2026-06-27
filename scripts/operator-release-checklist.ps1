# Pre-build operator checklist for Phase 12.5 (does not build or sign).
param(
    [switch]$RequireSigning
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$failures = @()
$warnings = @()

function Test-Command($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        $script:failures += "Missing command: $name"
    }
}

Write-Host "CoinWallet release checklist (Phase 12.5)" -ForegroundColor Cyan
Write-Host ""

Test-Command "node"
Test-Command "npm"
Test-Command "cargo"

if (-not (Test-Path "venv\Scripts\python.exe")) {
    $failures += "Python venv missing - run setup.bat"
} else {
    Write-Host "Running pre-release security gate..." -ForegroundColor Cyan
    & (Join-Path $Root "venv\Scripts\python.exe") (Join-Path $PSScriptRoot "verify_release_security.py")
    if ($LASTEXITCODE -ne 0) {
        $failures += "verify_release_security.py failed"
    }
}

if (-not (Test-Path ".env.production.desktop.example")) {
    $warnings += "Missing .env.production.desktop.example"
}

$tauriVersion = (Get-Content "src-tauri\tauri.conf.json" -Raw | ConvertFrom-Json).version
Write-Host "Tauri package version: $tauriVersion" -ForegroundColor DarkGray

if (-not $env:WIN_SIGN_CERT_PATH) {
    $msg = "WIN_SIGN_CERT_PATH not set - Windows build will be unsigned"
    if ($RequireSigning) { $failures += $msg } else { $warnings += $msg }
}

if (-not $env:APPLE_SIGNING_IDENTITY) {
    $msg = "APPLE_SIGNING_IDENTITY not set - macOS build will be unsigned"
    if ($RequireSigning) { $failures += $msg } else { $warnings += $msg }
}

foreach ($w in $warnings) {
    Write-Host "WARN: $w" -ForegroundColor Yellow
}

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "Checklist FAILED:" -ForegroundColor Red
    foreach ($f in $failures) {
        Write-Host "  - $f" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "Checklist passed." -ForegroundColor Green
Write-Host ""
Write-Host "Build and publish:" -ForegroundColor Cyan
Write-Host "  .\scripts\build-windows.ps1          # Windows (signs if WIN_SIGN_CERT_PATH set)"
Write-Host "  ./scripts/build-mac.sh               # macOS (signs if APPLE_SIGNING_IDENTITY set)"
Write-Host "  .\scripts\finalize-release.ps1       # after manual manifest edits"
Write-Host "  .\scripts\deploy-site.ps1            # requires CLOUDFLARE_API_TOKEN"
Write-Host ""
Write-Host "Signing env (optional but recommended):" -ForegroundColor DarkGray
Write-Host "  WIN_SIGN_CERT_PATH, WIN_SIGN_CERT_PASSWORD, SIGNTOOL_PATH"
Write-Host "  APPLE_SIGNING_IDENTITY, APPLE_NOTARY_* for notarization"
Write-Host "  RELEASE_SIGNER_FINGERPRINT / RELEASE_SIGNER_FINGERPRINT_WINDOWS / _MACOS"

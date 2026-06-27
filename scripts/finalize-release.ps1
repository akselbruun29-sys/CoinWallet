# Post-build release finalization (Phase 12.5): verify hashes, sync site static, print deploy steps.
param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$python = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "venv not found - run setup.bat first."
}

Write-Host "Verifying release manifest hashes..." -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot "verify-release-manifest.py")
if ($LASTEXITCODE -ne 0) {
    Write-Error "Manifest verification failed - fix hashes before publishing."
}

Write-Host "Syncing manifest + artifacts to site/static/releases/..." -ForegroundColor Cyan
node (Join-Path $PSScriptRoot "sync-site-releases.mjs")
if ($LASTEXITCODE -ne 0) {
    Write-Error "sync-site-releases.mjs failed."
}

$manifest = Get-Content (Join-Path $Root "releases\releases.json") -Raw | ConvertFrom-Json
if (-not $Version) {
    $Version = $manifest.version
}

$available = @()
foreach ($key in @("windows", "macos")) {
    $p = $manifest.platforms.$key
    if ($p.available -and $p.sha256) {
        $available += $key
    }
}

Write-Host ""
Write-Host "Release $Version finalized locally." -ForegroundColor Green
if ($available.Count -eq 0) {
    Write-Host "No platforms marked available with checksums yet." -ForegroundColor Yellow
} else {
    Write-Host "Available platforms: $($available -join ', ')" -ForegroundColor Green
}

Write-Host ""
Write-Host "Operator next steps:" -ForegroundColor Cyan
Write-Host "  1. Commit releases/releases.json (and site/static/releases/ if you track synced copies)."
Write-Host "  2. Deploy:  .\scripts\deploy-site.ps1  (set CLOUDFLARE_API_TOKEN first)"
Write-Host "  3. Confirm /download shows checksums and download links for each available platform."
Write-Host "  4. Update signing-keys on site if publisher fingerprints changed."

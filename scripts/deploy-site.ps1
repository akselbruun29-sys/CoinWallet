# Deploy download site to Cloudflare Pages with release binaries (Phase 12.5).
param(
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if (-not $env:CLOUDFLARE_API_TOKEN) {
    Write-Error @"
CLOUDFLARE_API_TOKEN is not set.

Create a token at https://developers.cloudflare.com/fundamentals/api/get-started/create-token/
with Cloudflare Pages edit permission, then:

  `$env:CLOUDFLARE_API_TOKEN = '<token>'
  `$env:CLOUDFLARE_ACCOUNT_ID = '<account-id>'   # optional for wrangler pages deploy

Re-run: .\scripts\deploy-site.ps1
"@
}

$python = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "venv not found - run setup.bat first."
}

Write-Host "Syncing releases manifest and binaries..." -ForegroundColor Cyan
node (Join-Path $PSScriptRoot "sync-site-releases.mjs")

if (-not $SkipVerify) {
    & $python (Join-Path $PSScriptRoot "verify-release-manifest.py")
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Release manifest verification failed."
    }

    $manifest = Get-Content (Join-Path $Root "releases\releases.json") -Raw | ConvertFrom-Json
    foreach ($key in @("windows", "macos")) {
        $p = $manifest.platforms.$key
        if ($p.available -and $p.sha256) {
            $fileName = if ($key -eq "windows") { "coinwallet-windows-x64.exe" } else { "coinwallet-macos.dmg" }
            $path = Join-Path $Root "site\static\releases\$fileName"
            if (-not (Test-Path $path)) {
                Write-Error "Platform $key is available but $path is missing. Run finalize-release.ps1 after building."
            }
        }
    }
}

Write-Host "Building and deploying site..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "site")
try {
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run deploy:cf
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}

Write-Host "Deploy complete. Check /download for release links and checksums." -ForegroundColor Green

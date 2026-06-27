# Deploy download site to Cloudflare Pages with release binaries (Phase 12.5).
param(
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

function Test-WranglerAuth {
    Push-Location (Join-Path $Root "site")
    try {
        $out = npx wrangler whoami 2>&1 | Out-String
        return ($LASTEXITCODE -eq 0 -and $out -notmatch "not authenticated")
    } finally {
        Pop-Location
    }
}

if (-not $env:CLOUDFLARE_API_TOKEN -and -not (Test-WranglerAuth)) {
    Write-Error @"
Not authenticated for Cloudflare deploy.

Option A (easiest): run the one-time setup script (opens browser login):
  .\scripts\setup-cloudflare.ps1

Option B: log in manually:
  cd site
  npx wrangler login

Option C: use an API token instead:
  `$env:CLOUDFLARE_API_TOKEN = '<token>'
  `$env:CLOUDFLARE_ACCOUNT_ID = '<account-id>'

Create tokens: https://dash.cloudflare.com/profile/api-tokens
  -> Create Token -> Edit Cloudflare Workers (includes Pages Edit)
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
            $fileName = ($p.url -split '/')[-1]
            $path = Join-Path $Root "site\static\releases\$fileName"
            if (-not (Test-Path $path)) {
                Write-Error "Platform $key is available but $path is missing. Run finalize-release.ps1 after building."
            }
        }
    }
}

Write-Host "Building and deploying site..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "ensure-cloudflare-pages-project.ps1")
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

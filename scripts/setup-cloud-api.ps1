# Deploy CoinWallet cloud API (leaderboard) to Cloudflare Workers + D1.
# Run from repo root in PowerShell after Pages setup.
param(
    [switch]$SkipLogin,
    [switch]$SkipDeploy
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$CloudDir = Join-Path $Root "cloud"
Set-Location $Root

Write-Host ""
Write-Host "=== CoinWallet - Cloud API (Workers + D1) ===" -ForegroundColor Cyan
Write-Host ""

function Test-WranglerAuth {
    Push-Location $CloudDir
    try {
        $out = npx wrangler whoami 2>&1 | Out-String
        return ($LASTEXITCODE -eq 0 -and $out -notmatch "not authenticated")
    } finally {
        Pop-Location
    }
}

if (-not $env:CLOUDFLARE_API_TOKEN -and -not $SkipLogin -and -not (Test-WranglerAuth)) {
    Write-Host "Logging in to Wrangler (browser)..." -ForegroundColor Yellow
    Push-Location $CloudDir
    try {
        npx wrangler login
    } finally {
        Pop-Location
    }
}

Push-Location $CloudDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing cloud worker dependencies..." -ForegroundColor Cyan
        npm install
    }

    Write-Host "Creating D1 database (if needed)..." -ForegroundColor Cyan
    $dbList = npx wrangler d1 list 2>&1 | Out-String
    if ($dbList -notmatch "coinwallet-leaderboard") {
        npx wrangler d1 create coinwallet-leaderboard
        Write-Host ""
        Write-Host "Copy the database_id from above into cloud/wrangler.toml, then re-run this script." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "Applying D1 schema..." -ForegroundColor Cyan
    npx wrangler d1 execute coinwallet-leaderboard --remote --file=./schema.sql

    if (-not $SkipDeploy) {
        Write-Host "Deploying worker..." -ForegroundColor Cyan
        npx wrangler deploy
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1. Note the worker URL from wrangler deploy (e.g. https://coinwallet-api.<subdomain>.workers.dev)"
Write-Host "  2. Site build:  `$env:VITE_REMOTE_SERVICES_URL = '<worker-url>'"
Write-Host "  3. Desktop build: same env var before build-windows.ps1 (baked into admin UI + sidecar .env on first run)"
Write-Host "  4. GitHub Actions: set repo variable VITE_REMOTE_SERVICES_URL"
Write-Host ""

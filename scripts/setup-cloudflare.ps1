# One-time Cloudflare Pages setup + first deploy for the CoinWallet download site.
# Run from repo root in PowerShell (interactive - opens browser for wrangler login).
param(
    [switch]$SkipLogin,
    [switch]$SkipDeploy
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host ""
Write-Host "=== CoinWallet - Cloudflare Pages setup ===" -ForegroundColor Cyan
Write-Host ""

function Test-WranglerAuth {
    Push-Location (Join-Path $Root "site")
    try {
        $out = npx wrangler whoami 2>&1 | Out-String
        return ($LASTEXITCODE -eq 0 -and $out -notmatch "not authenticated")
    } finally {
        Pop-Location
    }
}

Write-Host "Step 1 - Cloudflare account (free)" -ForegroundColor Yellow
Write-Host "  If you do not have one, sign up at: https://dash.cloudflare.com/sign-up"
Write-Host "  No credit card required for Pages on the free tier."
Write-Host ""

Write-Host "Step 2 - Authenticate Wrangler (browser login)" -ForegroundColor Yellow
if ($env:CLOUDFLARE_API_TOKEN) {
    Write-Host "  CLOUDFLARE_API_TOKEN is set - skipping wrangler login." -ForegroundColor Green
}
elseif ($SkipLogin -or (Test-WranglerAuth)) {
    if (-not $SkipLogin) {
        Write-Host "  Already logged in to Wrangler." -ForegroundColor Green
    }
}
else {
    Write-Host "  A browser window will open. Approve access for Wrangler CLI."
    Write-Host "  Press Enter to continue..."
    Read-Host | Out-Null
    Push-Location (Join-Path $Root "site")
    try {
        npx wrangler login
        if ($LASTEXITCODE -ne 0) {
            Write-Error "wrangler login failed."
        }
    } finally {
        Pop-Location
    }
}

if (-not $env:CLOUDFLARE_API_TOKEN) {
    Write-Host ""
    Write-Host "Step 3 - Account ID (for GitHub Actions later, optional now)" -ForegroundColor Yellow
    Push-Location (Join-Path $Root "site")
    try {
        npx wrangler whoami
    } finally {
        Pop-Location
    }
    Write-Host ""
    Write-Host "  Copy the Account ID from the output above if you add GitHub Actions secrets later."
    Write-Host '  Dashboard: Workers and Pages -> Overview -> Account details -> Account ID'
}
else {
    if (-not $env:CLOUDFLARE_ACCOUNT_ID) {
        Write-Host ""
        Write-Host "  Tip: set CLOUDFLARE_ACCOUNT_ID too if GitHub Actions deploy fails." -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Step 4 - Install site dependencies" -ForegroundColor Yellow
Push-Location (Join-Path $Root "site")
try {
    if (-not (Test-Path "node_modules")) {
        npm install
    }
} finally {
    Pop-Location
}

if ($SkipDeploy) {
    Write-Host ""
    Write-Host "Setup complete (deploy skipped). Run: .\scripts\deploy-site.ps1" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Step 5 - Sync releases, build, deploy to project coinwallet" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "deploy-site.ps1")

Write-Host ""
Write-Host "Done. Your site URL is shown above (pages.dev)." -ForegroundColor Green
Write-Host "  /download - download page"
Write-Host "  /releases/coinwallet-windows-x64-setup.exe - Windows installer"
Write-Host ""
Write-Host 'Optional: Cloudflare dashboard -> Workers and Pages -> coinwallet -> Custom domains'

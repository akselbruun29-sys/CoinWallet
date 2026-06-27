# Ensure Cloudflare Pages project exists (non-interactive). Idempotent.
param(
    [string]$ProjectName = "coinwallet",
    [string]$ProductionBranch = "master"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Push-Location (Join-Path $Root "site")
try {
    $list = npx wrangler pages project list 2>&1 | Out-String
    if ($list -match [regex]::Escape($ProjectName)) {
        Write-Host "Cloudflare Pages project '$ProjectName' already exists." -ForegroundColor DarkGray
        return
    }

    Write-Host "Creating Cloudflare Pages project '$ProjectName'..." -ForegroundColor Cyan
    npx wrangler pages project create $ProjectName --production-branch $ProductionBranch
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create Pages project '$ProjectName'."
    }
    Write-Host "Created project '$ProjectName'." -ForegroundColor Green
} finally {
    Pop-Location
}

# Run CoinWallet cloud services (leaderboard only — no wallet API).
# Deploy this to a small VPS / Fly.io / Railway; point site + desktop at the URL.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not $env:LEADERBOARD_CLOUD_MODE) {
    $env:LEADERBOARD_CLOUD_MODE = "true"
}
if (-not $env:WALLET_DB) {
    $env:WALLET_DB = "leaderboard_cloud.db"
}
if (-not $env:CORS_ORIGINS) {
    $env:CORS_ORIGINS = "https://coinwallet.pages.dev,http://localhost:5174"
}

Write-Host "Starting CoinWallet cloud services on http://127.0.0.1:8010"
Write-Host "LEADERBOARD_CLOUD_MODE=$env:LEADERBOARD_CLOUD_MODE WALLET_DB=$env:WALLET_DB"

python -m uvicorn api.cloud_app:app --host 0.0.0.0 --port 8010

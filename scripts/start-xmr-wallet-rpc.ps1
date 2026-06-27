# Start monero-wallet-rpc for CoinWallet XMR sync (stagenet example).
# Install Monero CLI, then run monerod + wallet-rpc for your network.
#
# Stagenet (default for new XMR wallets):
#   monerod --stagenet --detach
#   monero-wallet-rpc --stagenet --rpc-bind-port 38088 --disable-rpc-login --wallet-dir ./xmr-wallets
#
# Testnet:
#   monero-wallet-rpc --testnet --rpc-bind-port 18083 --disable-rpc-login --wallet-dir ./xmr-wallets
#
# Set in .env (optional):
#   XMR_WALLET_RPC_URI=http://127.0.0.1:38088/json_rpc
$ErrorActionPreference = "Stop"

$Port = if ($env:XMR_WALLET_RPC_PORT) { $env:XMR_WALLET_RPC_PORT } else { "38088" }
$Network = if ($env:XMR_NETWORK) { $env:XMR_NETWORK } else { "stagenet" }
$WalletDir = Join-Path $PSScriptRoot "..\xmr-wallets"
New-Item -ItemType Directory -Force -Path $WalletDir | Out-Null

$flag = switch ($Network) {
    "testnet" { "--testnet" }
    "mainnet" { "" }
    default { "--stagenet" }
}

Write-Host "Starting monero-wallet-rpc ($Network) on port $Port ..." -ForegroundColor Cyan
Write-Host "Wallet files: $WalletDir" -ForegroundColor DarkGray

if ($flag) {
    & monero-wallet-rpc $flag --rpc-bind-port $Port --disable-rpc-login --wallet-dir $WalletDir
} else {
    & monero-wallet-rpc --rpc-bind-port $Port --disable-rpc-login --wallet-dir $WalletDir
}

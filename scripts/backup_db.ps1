# Backup wallet.db
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Db = if ($env:WALLET_DB) { $env:WALLET_DB } else { Join-Path $Root "wallet.db" }
$BackupDir = if ($env:BACKUP_DIR) { $env:BACKUP_DIR } else { Join-Path $Root "backups" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
if (-not (Test-Path $Db)) {
    Write-Error "No database at $Db"
}
Copy-Item $Db (Join-Path $BackupDir "wallet_$Stamp.db")
Write-Host "Backed up to $BackupDir\wallet_$Stamp.db"

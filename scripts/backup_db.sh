#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="${WALLET_DB:-$ROOT/wallet.db}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"
if [[ -f "$DB" ]]; then
  cp "$DB" "$BACKUP_DIR/wallet_${STAMP}.db"
  echo "Backed up to $BACKUP_DIR/wallet_${STAMP}.db"
else
  echo "No database at $DB"
  exit 1
fi

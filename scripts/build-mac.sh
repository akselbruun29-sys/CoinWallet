#!/usr/bin/env bash
# Build CoinWallet for macOS — admin UI + Tauri + copy to releases/
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Building CoinWallet for macOS..."

if [[ ! -x venv/bin/python ]]; then
  echo "Run setup.sh first." >&2
  exit 1
fi

if [[ ! -d admin/node_modules ]]; then
  (cd admin && npm install)
fi

echo "Building admin UI (desktop)..."
npm run build:desktop --prefix admin

echo "Building Tauri bundle..."
cargo tauri build

DMG=$(find src-tauri/target/release/bundle/dmg -name '*.dmg' | head -n 1)
if [[ -z "$DMG" ]]; then
  echo "No .dmg found in src-tauri/target/release/bundle/dmg" >&2
  exit 1
fi

mkdir -p releases
cp "$DMG" releases/coinwallet-macos.dmg
echo "Copied to releases/coinwallet-macos.dmg"

VERSION=$(python -c "import json; print(json.load(open('src-tauri/tauri.conf.json'))['version'])")
powershell.exe -File scripts/update-releases-manifest.ps1 -Version "$VERSION" -MarkAvailable 2>/dev/null \
  || pwsh -File scripts/update-releases-manifest.ps1 -Version "$VERSION" -MarkAvailable 2>/dev/null \
  || python scripts/update_releases_manifest.py --version "$VERSION" --mark-available

echo "Done."

#!/usr/bin/env bash
# Post-build release finalization (Phase 12.5): verify hashes, sync site static, print deploy steps.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -x venv/bin/python ]]; then
  echo "venv not found — run setup.sh first." >&2
  exit 1
fi

echo "Verifying release manifest hashes..."
./venv/bin/python scripts/verify-release-manifest.py

echo "Syncing manifest + artifacts to site/static/releases/..."
node scripts/sync-site-releases.mjs

version=$(python -c "import json; print(json.load(open('releases/releases.json'))['version'])")
available=$(python - <<'PY'
import json
data = json.load(open("releases/releases.json"))
keys = [k for k, p in data.get("platforms", {}).items() if p.get("available") and p.get("sha256")]
print(", ".join(keys) if keys else "")
PY
)

echo ""
echo "Release ${version} finalized locally."
if [[ -z "$available" ]]; then
  echo "No platforms marked available with checksums yet."
else
  echo "Available platforms: ${available}"
fi

echo ""
echo "Operator next steps:"
echo "  1. Commit releases/releases.json (and site/static/releases/ if you track synced copies)."
echo "  2. Deploy the download site:  cd site && npm run deploy:cf"
echo "     (or push to main — deploy-site.yml runs when releases/ changes)."
echo "  3. Confirm /download shows checksums and download links for each available platform."
echo "  4. Update signing-keys on site if publisher fingerprints changed."

#!/usr/bin/env bash
# Deploy download site to Cloudflare Pages with release binaries (Phase 12.5).
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "CLOUDFLARE_API_TOKEN is not set." >&2
  echo "Create a token with Cloudflare Pages edit permission, export it, then re-run." >&2
  exit 1
fi

if [[ ! -x venv/bin/python ]]; then
  echo "venv not found - run setup.sh first." >&2
  exit 1
fi

echo "Syncing releases manifest and binaries..."
node scripts/sync-site-releases.mjs

if [[ "${SKIP_VERIFY:-}" != "1" ]]; then
  ./venv/bin/python scripts/verify-release-manifest.py
fi

echo "Building and deploying site..."
(
  cd site
  if [[ ! -d node_modules ]]; then npm install; fi
  npm run deploy:cf
)

echo "Deploy complete. Check /download for release links and checksums."

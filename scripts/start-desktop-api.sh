#!/usr/bin/env bash
# Start the local wallet API for desktop dev (127.0.0.1 only)
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -x venv/bin/python ]]; then
  echo "Run setup.sh first to create the virtual environment." >&2
  exit 1
fi

export STRICT_SECRETS=true
exec ./venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8002

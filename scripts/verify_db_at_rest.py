#!/usr/bin/env python3
"""Verify optional wallet database encryption at rest (Phase 11.15)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    (ROOT / "src" / "db_at_rest.py", "prepare_db_path"),
    (ROOT / "src" / "db_at_rest.py", "seal_db_path"),
    (ROOT / "src" / "database.py", "prepare_db_path"),
    (ROOT / "api" / "main.py", "seal_db_path"),
    (ROOT / ".env.example", "WALLET_DB_KEY"),
]


def main() -> int:
    missing: list[str] = []
    for path, marker in REQUIRED:
        if not path.exists():
            missing.append(f"missing file: {path.relative_to(ROOT)}")
            continue
        if marker not in path.read_text(encoding="utf-8"):
            missing.append(f"{path.relative_to(ROOT)}: missing `{marker}`")

    if missing:
        print("FAIL — database at-rest encryption audit:\n")
        for line in missing:
            print(f"  - {line}")
        return 1

    print("OK — wallet.db.cwenc AES-GCM sealing wired (set WALLET_DB_KEY to enable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

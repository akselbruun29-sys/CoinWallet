#!/usr/bin/env python3
"""Audit mainnet safety gates (Phase 9.3)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKERS = [
    (ROOT / "src" / "wallet" / "mainnet_gate.py", "ensure_mainnet_ready"),
    (ROOT / "src" / "wallet" / "core.py", "ensure_mainnet_ready"),
    (ROOT / "src" / "wallet" / "core.py", "ensure_wallet_mainnet_ready"),
    (ROOT / "src" / "database.py", "mainnet_ack_at"),
    (ROOT / "api" / "security.py", "/wallet/mainnet/acknowledge"),
    (ROOT / "api" / "admin.py", "mainnet_enable_acknowledged"),
]


def main() -> int:
    missing: list[str] = []
    for path, marker in REQUIRED_MARKERS:
        if not path.exists():
            missing.append(f"missing file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        if marker not in text:
            missing.append(f"{path.relative_to(ROOT)}: missing `{marker}`")

    if missing:
        print("FAIL — mainnet gate audit:\n")
        for line in missing:
            print(f"  - {line}")
        return 1

    print("OK — mainnet gates: v2 passphrase, user ack, admin enable ack")
    return 0


if __name__ == "__main__":
    sys.exit(main())

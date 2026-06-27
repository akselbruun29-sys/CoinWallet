#!/usr/bin/env python3
"""Verify XMR secrets are never exposed via API responses (Phase 11.28)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "api"

FORBIDDEN_RESPONSE_KEYS = (
    "xmr_encrypted_view_key",
    "encrypted_seed",
    "encrypted_view_key",
    "secret_view_key",
    "secret_spend_key",
    "spend_key",
    "view_key",
    "private_spend",
    "private_view",
)

RETURN_FORBIDDEN = re.compile(
    r"return\s+\{[\s\S]{0,600}?(?:"
    + "|".join(re.escape(k) for k in FORBIDDEN_RESPONSE_KEYS)
    + r")",
    re.MULTILINE,
)

MNEMONIC_FORBIDDEN_OUTSIDE_CREATE = re.compile(
    r"@router\.(get|patch|put|delete)\([^\)]*\)[\s\S]{0,400}?return[\s\S]{0,200}?[\"']mnemonic[\"']",
    re.MULTILINE,
)


def main() -> int:
    hits: list[str] = []

    db_path = ROOT / "src" / "database.py"
    if db_path.exists():
        db_text = db_path.read_text(encoding="utf-8")
        if "_WALLET_PUBLIC_COLUMNS" in db_text:
            block = db_text.split("_WALLET_PUBLIC_COLUMNS", 1)[1].split('"""', 2)[1]
            for key in FORBIDDEN_RESPONSE_KEYS:
                if key in block:
                    hits.append(f"database.py _WALLET_PUBLIC_COLUMNS includes forbidden `{key}`")
        else:
            hits.append("database.py: missing _WALLET_PUBLIC_COLUMNS wallet projection")

    if API_DIR.exists():
        for path in sorted(API_DIR.rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8", errors="ignore")
            if RETURN_FORBIDDEN.search(text):
                hits.append(f"{rel}: return payload may include forbidden wallet secret keys")
            if MNEMONIC_FORBIDDEN_OUTSIDE_CREATE.search(text):
                hits.append(f"{rel}: mnemonic may be returned outside create-wallet POST")

    xmr_keys = ROOT / "src" / "wallet" / "xmr" / "keys.py"
    if xmr_keys.exists():
        text = xmr_keys.read_text(encoding="utf-8")
        if "never expose via api" not in text.lower():
            hits.append("src/wallet/xmr/keys.py: missing API exposure guard comment")

    if hits:
        print("FAIL — XMR / wallet secret API exposure audit:\n")
        for line in hits:
            print(f"  - {line}")
        return 1

    print("OK — API wallet projections omit XMR view/spend keys and encrypted seeds")
    print("OK — Phase 11.28 XMR secret exposure audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

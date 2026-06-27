#!/usr/bin/env python3
"""Audit backup flow — mnemonic shown once at create (Phase 9.4)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WALLET_API = ROOT / "api" / "wallet.py"
ADMIN_SRC = ROOT / "admin" / "src"

FORBIDDEN_RESPONSE_PATTERNS = [
    re.compile(r'@router\.(get|delete)[^\n]*\n(?:.*\n){0,20}.*["\']mnemonic["\']', re.M),
    re.compile(r'return\s*\{[^}]*["\']mnemonic["\']', re.M),
]

ALLOWLIST_CREATE = re.compile(
    r'@router\.post\(""\)[\s\S]*?return\s*\{\*\*wallet,\s*"mnemonic":\s*mnemonic\}'
)


def main() -> int:
    hits: list[str] = []

    if not WALLET_API.exists():
        print("FAIL — api/wallet.py not found")
        return 1

    wallet_text = WALLET_API.read_text(encoding="utf-8")
    if '"mnemonic": mnemonic' not in wallet_text:
        hits.append("create_wallet must return mnemonic once on POST /api/wallets")

    export_block = re.search(
        r'@router\.get\("/\{wallet_id\}/export"\)[\s\S]*?return\s*\{[^}]+\}',
        wallet_text,
    )
    if export_block and "mnemonic" in export_block.group(0):
        hits.append("export_wallet must not return mnemonic")

    list_get_blocks = re.findall(
        r'@router\.get[^\n]*\n(?:.*\n){0,25}?return[^\n]+',
        wallet_text,
    )
    for block in list_get_blocks:
        if "mnemonic" in block and "export" not in block:
            hits.append(f"GET route may expose mnemonic: {block[:80]}...")

    wallets_page = ADMIN_SRC / "routes" / "(app)" / "wallets" / "+page.svelte"
    if wallets_page.exists():
        ui = wallets_page.read_text(encoding="utf-8")
        if "backupConfirmed" not in ui:
            hits.append("wallets UI must require backup confirmation checkbox")
        if "mnemonic = ''" not in ui.replace(" ", ""):
            if "mnemonic = '';" not in ui and "mnemonic = \"\";" not in ui:
                hits.append("wallets UI should clear mnemonic after backup dialog closes")

    if hits:
        print("FAIL — backup flow audit:\n")
        for line in hits:
            print(f"  - {line}")
        return 1

    print("OK — mnemonic returned only on wallet create; export has no seed; UI confirms backup")
    return 0


if __name__ == "__main__":
    sys.exit(main())

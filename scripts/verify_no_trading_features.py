#!/usr/bin/env python3
"""Verify CoinWallet has no trading-bot, signal, or background-swap features (Phase 8.8)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_DIRS = ("api", "src", "admin/src")
SKIP_SUFFIXES = {".md", ".json", ".svg", ".png", ".ico", ".lock", ".pyc"}
SKIP_DIR_NAMES = {"__pycache__", "node_modules", ".svelte-kit", "build", "dist"}

# Patterns that indicate forbidden product features (not policy disclaimers).
FORBIDDEN = [
    (re.compile(r"\bexecute_trade\b"), "automated trade execution"),
    (re.compile(r"\bauto_trade\b"), "automated trading"),
    (re.compile(r"\btrading_bot\b"), "trading bot module"),
    (re.compile(r"\bbuy_signal\b|\bsell_signal\b"), "market signals"),
    (re.compile(r"\bbackground_swap\b"), "background swap job"),
    (re.compile(r"\bauto_swap\b"), "automated swap"),
    (re.compile(r"\bportfolio_rebalanc", re.I), "portfolio rebalancing bot"),
]

ALLOWLIST_FILES = {
    "scripts/verify_no_trading_features.py",
}


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for name in SCAN_DIRS:
        base = ROOT / name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if path.suffix.lower() in SKIP_SUFFIXES:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in ALLOWLIST_FILES:
                continue
            files.append(path)
    return files


def main() -> int:
    hits: list[str] = []
    for path in iter_source_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern, label in FORBIDDEN:
            if pattern.search(text):
                hits.append(f"{rel}: matches forbidden pattern ({label})")

    if hits:
        print("FAIL — forbidden trading/automation patterns found:\n")
        for line in hits:
            print(f"  - {line}")
        return 1

    print("OK — no trading bot, signal, or background swap patterns in api/, src/, admin/src/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

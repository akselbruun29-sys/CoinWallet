#!/usr/bin/env python3
"""Verify release artifact SHA-256 hashes match releases/releases.json (Phase 11.4)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "releases" / "releases.json"

ARTIFACTS = {
    "windows": "coinwallet-windows-x64.exe",
    "macos": "coinwallet-macos.dmg",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not MANIFEST.exists():
        print(f"FAIL — manifest missing: {MANIFEST}")
        return 1

    data = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    errors: list[str] = []

    for key, filename in ARTIFACTS.items():
        platform = data.get("platforms", {}).get(key, {})
        expected = platform.get("sha256")
        path = ROOT / "releases" / filename
        if not path.exists():
            if expected:
                errors.append(f"{key}: manifest has sha256 but file missing ({path})")
            continue
        actual = sha256(path)
        if not expected:
            errors.append(f"{key}: file exists but manifest sha256 is null")
            continue
        if expected.lower() != actual.lower():
            errors.append(f"{key}: hash mismatch manifest={expected} actual={actual}")

    if errors:
        print("FAIL — release manifest verification errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("OK — release artifacts match releases/releases.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

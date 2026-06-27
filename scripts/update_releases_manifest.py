#!/usr/bin/env python3
"""Update releases/releases.json with SHA-256 hashes (cross-platform helper)."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "releases" / "releases.json"
SITE_MANIFEST = ROOT / "site" / "static" / "releases" / "releases.json"

ARTIFACTS = {
    "windows": ("coinwallet-windows-x64.exe", "/releases/coinwallet-windows-x64.exe"),
    "macos": ("coinwallet-macos.dmg", "/releases/coinwallet-macos.dmg"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--mark-available", action="store_true")
    args = parser.parse_args()

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["version"] = args.version
    data["released_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for key, (filename, url) in ARTIFACTS.items():
        path = ROOT / "releases" / filename
        if not path.exists():
            print(f"Skip {key} — not found: {path}")
            continue
        data["platforms"][key]["url"] = url
        data["platforms"][key]["sha256"] = sha256(path)
        if args.mark_available:
            data["platforms"][key]["available"] = True
        print(f"Updated {key}")

    text = json.dumps(data, indent=2) + "\n"
    MANIFEST.write_text(text, encoding="utf-8")
    SITE_MANIFEST.write_text(text, encoding="utf-8")
    print("Manifest updated.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Update releases/releases.json with SHA-256 hashes (cross-platform helper)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "releases" / "releases.json"
SITE_MANIFEST = ROOT / "site" / "static" / "releases" / "releases.json"
ARTIFACTS_META = ROOT / "scripts" / "release-artifacts.json"

sys.path.insert(0, str(ROOT / "scripts"))
from release_urls import load_artifacts_meta, resolve_platform_url

ARTIFACTS = load_artifacts_meta()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _macos_signature_status(path: Path) -> tuple[str, str | None]:
    try:
        proc = subprocess.run(
            ["codesign", "-dv", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and "Authority=" in (proc.stderr or proc.stdout):
            for line in (proc.stderr or proc.stdout).splitlines():
                if "Authority=" in line:
                    return "signed", line.split("Authority=", 1)[1].strip()
            return "signed", None
    except OSError:
        pass
    return "unsigned", None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--mark-available", action="store_true")
    parser.add_argument("--release-notes", default="")
    parser.add_argument("--signature-status", default="")
    args = parser.parse_args()

    data = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    data["version"] = args.version
    data["released_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.release_notes:
        data["release_notes"] = args.release_notes

    global_fp = os.getenv("RELEASE_SIGNER_FINGERPRINT")
    if global_fp:
        data["signer_fingerprint"] = global_fp

    for key, meta in ARTIFACTS.items():
        if key in ("github_repo", "cf_pages_max_mib"):
            continue
        filename = meta["filename"]
        path = ROOT / "releases" / filename
        if not path.exists():
            print(f"Skip {key} — not found: {path}")
            continue
        url = resolve_platform_url(key, version=args.version, artifact_path=path)
        data["platforms"][key]["url"] = url
        data["platforms"][key]["sha256"] = sha256(path)
        if args.mark_available:
            data["platforms"][key]["available"] = True

        env_fp = os.getenv(f"RELEASE_SIGNER_FINGERPRINT_{key.upper()}")
        if env_fp:
            data["platforms"][key]["signer_fingerprint"] = env_fp

        if args.signature_status:
            data["platforms"][key]["signature_status"] = args.signature_status
        elif key == "macos":
            status, authority = _macos_signature_status(path)
            data["platforms"][key]["signature_status"] = status
            if authority and not data["platforms"][key].get("signer_fingerprint"):
                data["platforms"][key]["signer_fingerprint"] = authority
        elif not data["platforms"][key].get("signature_status"):
            data["platforms"][key]["signature_status"] = "unsigned"

        print(f"Updated {key}")

    text = json.dumps(data, indent=2) + "\n"
    MANIFEST.write_text(text, encoding="utf-8")
    SITE_MANIFEST.write_text(text, encoding="utf-8")
    print("Manifest updated.")


if __name__ == "__main__":
    main()

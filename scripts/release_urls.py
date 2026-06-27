#!/usr/bin/env python3
"""Resolve download URL — GitHub Releases for artifacts over Cloudflare Pages limit."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_PATH = ROOT / "scripts" / "release-artifacts.json"
CF_PAGES_MAX_BYTES = 24 * 1024 * 1024


def load_artifacts_meta() -> dict:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def github_release_url(repo: str, version: str, filename: str) -> str:
    tag = version if version.startswith("v") else f"v{version}"
    return f"https://github.com/{repo}/releases/download/{tag}/{filename}"


def resolve_platform_url(
    platform_key: str,
    *,
    version: str,
    artifact_path: Path | None = None,
) -> str:
    meta = load_artifacts_meta()
    platform = meta[platform_key]
    filename = platform["filename"]
    local_url = platform["url"]

    use_github = bool(platform.get("host_on_github_releases"))
    if artifact_path and artifact_path.exists():
        if artifact_path.stat().st_size > CF_PAGES_MAX_BYTES:
            use_github = True

    if not use_github:
        return local_url

    repo = meta.get("github_repo") or ""
    if not repo:
        return local_url
    return github_release_url(repo, version, filename)

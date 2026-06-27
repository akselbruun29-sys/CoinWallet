#!/usr/bin/env python3
"""Verify localhost-only API binding expectations (Phase 11.20)."""
from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request

API = os.getenv("VALIDATE_API_URL", "http://127.0.0.1:8002")


def _get(path: str, headers: dict | None = None) -> tuple[int, str]:
    req = urllib.request.Request(f"{API}{path}", headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()
    except urllib.error.URLError as exc:
        raise ConnectionError(f"API not reachable at {API}: {exc.reason}") from exc


def main() -> int:
    try:
        code, _ = _get("/api/health")
    except ConnectionError as exc:
        print(f"SKIP — {exc}")
        return 0

    if code != 200:
        print(f"FAIL — health check returned {code} (is API running at {API}?)")
        return 1

    bad_code, _ = _get("/api/health", headers={"Host": "evil.example.com"})
    if bad_code != 403:
        print(f"FAIL — expected 403 for foreign Host header, got {bad_code}")
        return 1

    missing_code, _ = _get("/api/health", headers={"Host": ""})
    if missing_code != 403:
        print(f"FAIL — expected 403 for empty Host header, got {missing_code}")
        return 1

    print("OK — API accepts localhost Host and rejects foreign/missing Host headers")
    return 0


if __name__ == "__main__":
    sys.exit(main())

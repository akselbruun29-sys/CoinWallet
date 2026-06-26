#!/usr/bin/env python3
"""Automated API checks for multi-user wallet isolation (run with API on :8001)."""
from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
import json

API = os.getenv("VALIDATE_API_URL", "http://127.0.0.1:8002")


def req(method: str, path: str, token: str | None = None, body: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode()
    request = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode()
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"detail": payload}


def login(username: str, password: str) -> str:
    code, data = req("POST", "/api/auth/login", body={"username": username, "password": password})
    if code != 200 or "token" not in data:
        raise RuntimeError(f"Login failed for {username}: {data}")
    return data["token"]


def main() -> int:
    print(f"Wallet Vault isolation checks -> {API}")
    code, health = req("GET", "/api/health")
    if code != 200:
        print("FAIL: API not healthy", health)
        return 1
    print("OK: /api/health")

    admin_user = os.getenv("VALIDATE_ADMIN_USER", "admin")
    admin_pass = os.getenv("VALIDATE_ADMIN_PASS", os.getenv("ADMIN_PASSWORD", "changeme"))
    admin_token = login(admin_user, admin_pass)

    code, wallets = req("GET", "/api/wallets", admin_token)
    if code != 200:
        print("FAIL: admin cannot list own wallets", wallets)
        return 1
    admin_wallet_id = wallets[0]["id"] if wallets else None
    print(f"OK: admin wallets ({len(wallets)})")

    # Admin must not access arbitrary wallet IDs belonging to others (404)
    probe_id = (admin_wallet_id or 0) + 9999
    code, probe = req("GET", f"/api/wallets/{probe_id}", admin_token)
    if code != 404:
        print("FAIL: expected 404 for foreign wallet id", code, probe)
        return 1
    print("OK: foreign wallet id returns 404")

    # Security endpoints exist
    code, sec = req("GET", "/api/security/wallet", admin_token)
    if code != 200:
        print("FAIL: security status", sec)
        return 1
    print(
        f"OK: security status (passphrase={sec.get('has_wallet_passphrase')}, "
        f"legacy={sec.get('legacy_wallet_count', 0)})"
    )

    # Non-admin user isolation if test credentials provided
    test_user = os.getenv("VALIDATE_TEST_USER")
    test_pass = os.getenv("VALIDATE_TEST_PASS")
    if test_user and test_pass:
        user_token = login(test_user, test_pass)
        if admin_wallet_id:
            code, cross = req("GET", f"/api/wallets/{admin_wallet_id}", user_token)
            if code != 404:
                print("FAIL: user accessed admin wallet", code, cross)
                return 1
            print("OK: user cannot read admin wallet")
        code, uw = req("GET", "/api/wallets", user_token)
        if code != 200:
            print("FAIL: user wallet list", uw)
            return 1
        print(f"OK: test user wallets ({len(uw)})")

    # Logs admin-only
    code, logs = req("GET", "/api/logs", admin_token)
    if code != 200:
        print("FAIL: admin logs", logs)
        return 1
    if test_user and test_pass:
        code, _ = req("GET", "/api/logs", user_token)
        if code != 403:
            print("FAIL: non-admin should not read logs")
            return 1
        print("OK: logs admin-only")

    print("\nAll automated isolation checks passed.")
    print("Manual testnet flow: see docs/TESTNET_CHECKLIST.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

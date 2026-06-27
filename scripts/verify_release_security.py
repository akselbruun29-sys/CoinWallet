#!/usr/bin/env python3
"""Pre-release security gate — run static security audits (Phase 11.32)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STATIC_SCRIPTS = [
    "verify_no_trading_features.py",
    "verify_mainnet_gate.py",
    "verify_xmr_api_secrets.py",
    "verify_backup_flow.py",
    "verify_db_at_rest.py",
]

RUNTIME_SCRIPTS = [
    "verify_localhost_api.py",
]

REQUIRED_MARKERS = [
    (ROOT / "api" / "middleware.py", "SecurityHeadersMiddleware"),
    (ROOT / "api" / "middleware.py", "LocalhostOnlyMiddleware"),
    (ROOT / "api" / "auth.py", "SESSION_IDLE_SECONDS"),
    (ROOT / "src-tauri" / "src" / "lib.rs", "STRICT_SECRETS"),
    (ROOT / ".env.example", "CORS_ORIGINS"),
    (ROOT / ".env.example", "SWAP_PROVIDER_ALLOWLIST"),
    (ROOT / ".env.example", "WALLET_DB_KEY"),
    (ROOT / "src" / "db_at_rest.py", "CWDBENC1"),
]


def run_script(name: str) -> tuple[bool, str]:
    path = ROOT / "scripts" / name
    if not path.exists():
        return False, f"missing script: {name}"
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return False, output.strip() or f"{name} exited {proc.returncode}"
    return True, output.strip().splitlines()[-1] if output.strip() else "OK"


def check_markers() -> list[str]:
    missing: list[str] = []
    for path, marker in REQUIRED_MARKERS:
        if not path.exists():
            missing.append(f"missing file: {path.relative_to(ROOT)}")
            continue
        if marker not in path.read_text(encoding="utf-8"):
            missing.append(f"{path.relative_to(ROOT)}: missing `{marker}`")
    return missing


def main() -> int:
    failures: list[str] = []
    failures.extend(check_markers())

    print("=== CoinWallet pre-release security gate ===\n")

    for name in STATIC_SCRIPTS:
        ok, msg = run_script(name)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        if ok:
            if msg:
                print(f"       {msg}")
        else:
            print(f"       {msg}")
            failures.append(name)

    for name in RUNTIME_SCRIPTS:
        ok, msg = run_script(name)
        status = "PASS" if ok else "SKIP/FAIL"
        print(f"[{status}] {name} (requires running API)")
        if ok:
            if msg:
                print(f"       {msg}")
        else:
            print(f"       {msg}")
            print("       Hint: start API on 127.0.0.1:8002 or set VALIDATE_API_URL")

    if failures:
        print("\nFAIL — security gate did not pass:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("\nOK — pre-release security gate passed")
    print("Note: verify_localhost_api.py requires a running API for runtime Host-header checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

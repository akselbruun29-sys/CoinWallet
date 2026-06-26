"""Debug login issues."""
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

import bcrypt
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE = os.getenv("VALIDATE_API_URL", "http://127.0.0.1:8002")


def main() -> None:
    print("=== Health ===")
    try:
        with urllib.request.urlopen(f"{BASE}/api/health", timeout=3) as r:
            print(r.read().decode())
    except Exception as exc:
        print("FAIL:", exc)
        return

    print("\n=== .env auth ===")
    username = os.getenv("ADMIN_USERNAME", "admin")
    pw_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip().strip('"').strip("'")
    print("ADMIN_USERNAME:", username)
    print("ADMIN_PASSWORD_HASH set:", bool(pw_hash))
    for pw in ("changeme", "admin", "password"):
        if pw_hash:
            print(f"  matches {pw!r}:", bcrypt.checkpw(pw.encode(), pw_hash.encode()))

    print("\n=== Databases ===")
    from src.database import WalletDatabase

    db = WalletDatabase()
    print("WalletDatabase path:", db.db_path)
    print("User count:", db.count_users())
    for u in db.list_users():
        print(" ", u)

    print("\n=== Login API ===")
    for pw in ("changeme", "admin"):
        body = json.dumps({"username": username, "password": pw}).encode()
        req = urllib.request.Request(
            f"{BASE}/api/auth/login",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                print(f"  {pw!r}: OK role={data.get('role')}")
        except urllib.error.HTTPError as exc:
            print(f"  {pw!r}: HTTP {exc.code}", exc.read().decode()[:200])


if __name__ == "__main__":
    main()

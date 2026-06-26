"""Seed the initial admin user from environment variables."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    from src.database import WalletDatabase

    db = WalletDatabase()

    if db.count_users() > 0:
        users = db.list_users()
        print(f"Database already has {len(users)} user(s):")
        for u in users:
            print(f"  - {u['username']} ({u['role']})")
        return

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip().strip('"').strip("'")

    if not password_hash and not password:
        print("No users found. Set ADMIN_PASSWORD or ADMIN_PASSWORD_HASH in .env")
        print("Or run: python scripts/hash_password.py yourpassword")
        sys.exit(1)

    if not password_hash:
        import bcrypt

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user_id = db.create_user(username, password_hash, role="admin")
    print(f"Created admin user: {username} (id={user_id})")


if __name__ == "__main__":
    main()

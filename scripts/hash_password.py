"""Generate bcrypt password hash for user accounts in .env."""
import sys

import bcrypt

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/hash_password.py YOUR_PASSWORD")
        sys.exit(1)

    password = sys.argv[1]
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    print(hashed)
    print()
    print('Add to .env (use double quotes around the hash):')
    print(f'ADMIN_PASSWORD_HASH="{hashed}"')

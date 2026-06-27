"""Frozen desktop API entry — local uvicorn on 127.0.0.1 with per-user app data."""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path


def app_data_dir() -> Path:
    custom = os.environ.get("COINWALLET_APP_DATA", "").strip()
    if custom:
        return Path(custom)
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(base) / "CoinWallet"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "CoinWallet"
    return Path.home() / ".coinwallet"


def _select_port() -> int:
    raw = os.environ.get("COINWALLET_API_PORT", "8002").strip()
    try:
        return int(raw)
    except ValueError:
        return 8002


def ensure_production_env(app_data: Path) -> Path:
    env_path = app_data / ".env"
    if env_path.exists():
        return env_path

    app_data.mkdir(parents=True, exist_ok=True)
    admin_password = secrets.token_urlsafe(12)
    remote_url = os.environ.get("COINWALLET_REMOTE_SERVICES_URL", "").strip()
    lines = [
        "STRICT_SECRETS=true",
        "COINWALLET_PRODUCTION=true",
        "LOCALHOST_ONLY=true",
        f"SESSION_SECRET={secrets.token_urlsafe(32)}",
        f"WALLET_ENCRYPTION_KEY={secrets.token_urlsafe(48)}",
        f"WALLET_DB_KEY={secrets.token_urlsafe(32)}",
        "WALLET_DB=wallet.db",
        "BITCOIN_NETWORK=testnet",
        "TOR_ENABLED=true",
        "HTTP_PROXY=socks5h://127.0.0.1:9050",
        "HTTPS_PROXY=socks5h://127.0.0.1:9050",
        "TOR_SOCKS_PROXY=socks5h://127.0.0.1:9050",
        "OPEN_REGISTRATION=true",
        "AUTO_APPROVE_USERS=true",
        "ADMIN_USERNAME=admin",
        f"ADMIN_PASSWORD={admin_password}",
    ]
    if remote_url:
        lines.append(f"COINWALLET_REMOTE_SERVICES_URL={remote_url}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (app_data / "FIRST_RUN_SETUP.txt").write_text(
        "CoinWallet first-run admin login (change password after login):\n\n"
        f"  Username: admin\n"
        f"  Password: {admin_password}\n\n"
        "Stored only on this device. Delete this file after changing the password.\n",
        encoding="utf-8",
    )
    return env_path


def main() -> None:
    app_data = app_data_dir()
    app_data.mkdir(parents=True, exist_ok=True)
    os.chdir(app_data)

    env_file = ensure_production_env(app_data)
    from dotenv import load_dotenv

    load_dotenv(env_file, override=False)
    os.environ.setdefault("STRICT_SECRETS", "true")
    os.environ.setdefault("COINWALLET_PRODUCTION", "true")
    os.environ.setdefault("LOCALHOST_ONLY", "true")
    os.environ["WALLET_DB"] = str(app_data / "wallet.db")
    os.environ.setdefault("COINWALLET_SERVE_UI", "true")

    if os.environ.get("COINWALLET_TOR_MANAGED", "").lower() in ("true", "1", "yes"):
        from src.database import WalletDatabase

        db = WalletDatabase()
        db.set_setting("tor_enabled", "true")
        if not db.get_setting("network_wizard_complete"):
            db.set_setting("network_wizard_complete", "false")

    host = os.environ.get("COINWALLET_API_HOST", "127.0.0.1")
    port = _select_port()

    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        log_level=os.environ.get("COINWALLET_API_LOG_LEVEL", "warning"),
    )


if __name__ == "__main__":
    main()

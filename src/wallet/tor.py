"""Tor SOCKS proxy helpers for wallet network traffic."""
from __future__ import annotations

import os
from typing import Any, Optional

import requests

DEFAULT_TOR_SOCKS = "socks5h://127.0.0.1:9050"


def tor_socks_url() -> str:
    return (
        os.getenv("TOR_SOCKS_PROXY", "").strip()
        or os.getenv("HTTP_PROXY", "").strip()
        or os.getenv("HTTPS_PROXY", "").strip()
        or DEFAULT_TOR_SOCKS
    )


def tor_enabled_for_db(db: Any | None) -> bool:
    if db is not None:
        setting = db.get_setting("tor_enabled", "").strip().lower()
        if setting in ("true", "1", "yes"):
            return True
        if setting in ("false", "0", "no"):
            return False
    return os.getenv("TOR_ENABLED", "false").lower() in ("true", "1", "yes")


def tor_proxies(db: Any | None = None) -> Optional[dict[str, str]]:
    if not tor_enabled_for_db(db):
        return None
    proxy = tor_socks_url()
    return {"http": proxy, "https": proxy}


def apply_tor_proxies(session: requests.Session, db: Any | None = None) -> None:
    proxies = tor_proxies(db)
    if proxies:
        session.proxies.update(proxies)


def tor_bootstrap_complete(db: Any | None = None, timeout: float = 12.0) -> bool:
    """Return True when outbound traffic via Tor reaches check.torproject.org."""
    proxies = tor_proxies(db)
    if not proxies:
        return False
    try:
        resp = requests.get(
            "https://check.torproject.org/api/ip",
            proxies=proxies,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("IsTor"))
    except Exception:
        return False

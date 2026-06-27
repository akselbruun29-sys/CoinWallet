"""Optional cloud services — leaderboard sync and config helpers."""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_REMOTE_TIMEOUT = 12


def remote_services_url() -> Optional[str]:
    raw = (os.getenv("COINWALLET_REMOTE_SERVICES_URL") or "").strip().rstrip("/")
    return raw or None


def leaderboard_cloud_mode() -> bool:
    return os.getenv("LEADERBOARD_CLOUD_MODE", "").lower() in ("true", "1", "yes")


def hash_leaderboard_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_leaderboard_token() -> str:
    return secrets.token_urlsafe(32)


def _post(path: str, payload: dict) -> Optional[dict]:
    base = remote_services_url()
    if not base:
        return None
    url = f"{base}{path}"
    try:
        res = requests.post(url, json=payload, timeout=_REMOTE_TIMEOUT)
        if res.status_code >= 400:
            logger.warning("Remote leaderboard %s failed: %s %s", path, res.status_code, res.text[:200])
            return None
        return res.json()
    except requests.RequestException as exc:
        logger.warning("Remote leaderboard %s error: %s", path, exc)
        return None


def remote_leaderboard_register(
    token: str, display_name: str, network: str, balance_sats: int,
) -> Optional[dict]:
    return _post(
        "/api/leaderboard/remote/register",
        {
            "token": token,
            "display_name": display_name,
            "network": network,
            "balance_sats": balance_sats,
        },
    )


def remote_leaderboard_update(token: str, network: str, balance_sats: int) -> Optional[dict]:
    return _post(
        "/api/leaderboard/remote/update",
        {"token": token, "network": network, "balance_sats": balance_sats},
    )


def remote_leaderboard_opt_out(token: str, network: str) -> None:
    _post("/api/leaderboard/remote/opt-out", {"token": token, "network": network})

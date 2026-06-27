"""Public leaderboard API — opt-in balance rankings only."""
from __future__ import annotations

import re
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.auth import AuthUser, get_current_user, get_db
from api.rate_limit import check_rate_limit
from api.remote_services import (
    new_leaderboard_token,
    remote_leaderboard_opt_out,
    remote_leaderboard_register,
    remote_leaderboard_update,
    remote_services_url,
    leaderboard_cloud_mode,
)
from src.database import WalletDatabase

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])

_CACHE_TTL_SECONDS = 30
_cache: dict[str, tuple[float, dict]] = {}
_last_balance_update: dict[str, float] = {}

_DISPLAY_NAME_RE = re.compile(r"^[A-Za-z0-9 _-]{2,32}$")
_RESERVED_NAMES = frozenset(
    {
        "admin",
        "administrator",
        "coinwallet",
        "official",
        "support",
        "moderator",
        "staff",
        "system",
        "root",
    }
)
_MAX_BALANCE_JUMP_RATIO = 2.0
_MIN_BALANCE_UPDATE_INTERVAL = 60


def validate_display_name(name: str) -> str:
    cleaned = name.strip()
    if not _DISPLAY_NAME_RE.fullmatch(cleaned):
        raise ValueError(
            "Display name must be 2–32 characters: letters, numbers, spaces, hyphen, underscore"
        )
    normalized = cleaned.lower().replace(" ", "").replace("-", "").replace("_", "")
    for reserved in _RESERVED_NAMES:
        if reserved in normalized:
            raise ValueError("Display name cannot impersonate admin or CoinWallet staff")
    return cleaned


def _cache_get(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if not entry:
        return None
    expires_at, payload = entry
    if time.time() > expires_at:
        _cache.pop(key, None)
        return None
    return payload


def _cache_set(key: str, payload: dict) -> None:
    _cache[key] = (time.time() + _CACHE_TTL_SECONDS, payload)


def push_leaderboard_balance(db: WalletDatabase, user_id: int, network: str) -> None:
    """Update stored balance when user is opted in (called after wallet sync)."""
    entry = db.get_leaderboard_entry(user_id, network)
    if not entry or not entry["opted_in"]:
        return
    balance = db.user_total_balance_sats(user_id, network)
    db.update_leaderboard_balance(user_id, network, balance)
    _cache.clear()

    token = entry.get("remote_token")
    if remote_services_url() and token:
        remote_leaderboard_update(token, network, balance)


class OptInRequest(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=32)
    opted_in: bool


class UpdateRequest(BaseModel):
    balance_sats: int = Field(..., ge=0)
    network: str = Field(..., pattern="^(testnet|signet|regtest|mainnet)$")


@router.get("")
def get_leaderboard(
    request: Request,
    network: str = Query(default="testnet", pattern="^(testnet|signet|regtest|mainnet)$"),
    limit: int = Query(default=100, ge=1, le=100),
    db: WalletDatabase = Depends(get_db),
):
    check_rate_limit(request, "leaderboard_get", limit=120, window_seconds=60)
    cache_key = f"{network}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return JSONResponse(
            cached,
            headers={"Cache-Control": f"public, max-age={_CACHE_TTL_SECONDS}"},
        )

    payload = {
        "network": network,
        "entries": (
            db.list_global_leaderboard(network, limit)
            if leaderboard_cloud_mode()
            else db.list_leaderboard(network, limit)
        ),
    }
    _cache_set(cache_key, payload)
    return JSONResponse(
        payload,
        headers={"Cache-Control": f"public, max-age={_CACHE_TTL_SECONDS}"},
    )


@router.get("/me")
def get_my_leaderboard(
    network: str = Query(default="testnet", pattern="^(testnet|signet|regtest|mainnet)$"),
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    entry = db.get_leaderboard_entry(user.id, network)
    if not entry or not entry["opted_in"]:
        return {
            "network": network,
            "opted_in": False,
            "display_name": None,
            "balance_sats": 0,
            "rank": None,
        }

    return {
        "network": network,
        "opted_in": True,
        "display_name": entry["display_name"],
        "balance_sats": entry["balance_sats"],
        "rank": db.get_leaderboard_rank(user.id, network),
    }


@router.post("/opt-in")
def leaderboard_opt_in(
    body: OptInRequest,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    settings = db.get_system_settings()
    network = settings.get("network", "testnet")

    if body.opted_in:
        try:
            display_name = validate_display_name(body.display_name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        balance = db.user_total_balance_sats(user.id, network)
        existing = db.get_leaderboard_entry(user.id, network)
        remote_token = (existing or {}).get("remote_token") or new_leaderboard_token()
        db.set_leaderboard_opt_in(
            user.id, network, display_name, True, balance, remote_token=remote_token
        )
        if remote_services_url():
            remote_leaderboard_register(remote_token, display_name, network, balance)
        db.add_audit(
            "LEADERBOARD_OPT_IN",
            user_id=user.id,
            details=f"network={network}",
        )
    else:
        existing = db.get_leaderboard_entry(user.id, network)
        token = (existing or {}).get("remote_token")
        if remote_services_url() and token:
            remote_leaderboard_opt_out(token, network)
        db.set_leaderboard_opt_in(user.id, network, "", False)
        db.add_audit(
            "LEADERBOARD_OPT_OUT",
            user_id=user.id,
            details=f"network={network}",
        )

    _cache.clear()
    rank = db.get_leaderboard_rank(user.id, network) if body.opted_in else None
    entry = db.get_leaderboard_entry(user.id, network)
    return {
        "network": network,
        "opted_in": body.opted_in,
        "display_name": entry["display_name"] if entry else None,
        "balance_sats": entry["balance_sats"] if entry else 0,
        "rank": rank,
    }


@router.post("/update")
def leaderboard_update(
    body: UpdateRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    check_rate_limit(request, "leaderboard_update")
    entry = db.get_leaderboard_entry(user.id, body.network)
    if not entry or not entry["opted_in"]:
        raise HTTPException(status_code=400, detail="Leaderboard opt-in required")

    update_key = f"{user.id}:{body.network}"
    now = time.time()
    last_update = _last_balance_update.get(update_key, 0)
    if now - last_update < _MIN_BALANCE_UPDATE_INTERVAL:
        raise HTTPException(
            status_code=429,
            detail="Leaderboard balance updates are limited to once per minute",
        )

    server_balance = db.user_total_balance_sats(user.id, body.network)
    tolerance = max(10_000, int(server_balance * 0.05))
    if abs(body.balance_sats - server_balance) > tolerance:
        raise HTTPException(
            status_code=400,
            detail="Reported balance does not match synced wallet total",
        )

    previous = int(entry.get("balance_sats") or 0)
    if previous > 0 and server_balance > previous * _MAX_BALANCE_JUMP_RATIO + tolerance:
        raise HTTPException(status_code=400, detail="Impossible balance increase rejected")

    if not db.update_leaderboard_balance(user.id, body.network, server_balance):
        raise HTTPException(status_code=400, detail="Leaderboard entry not found")

    _last_balance_update[update_key] = now
    _cache.clear()
    return {
        "network": body.network,
        "balance_sats": server_balance,
        "rank": db.get_leaderboard_rank(user.id, body.network),
    }

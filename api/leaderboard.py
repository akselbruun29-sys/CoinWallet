"""Public leaderboard API — opt-in balance rankings only."""
from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from api.auth import AuthUser, get_current_user, get_db
from api.rate_limit import check_rate_limit
from src.database import WalletDatabase

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])

_CACHE_TTL_SECONDS = 30
_cache: dict[str, tuple[float, dict]] = {}


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
        return cached

    payload = {
        "network": network,
        "entries": db.list_leaderboard(network, limit),
    }
    _cache_set(cache_key, payload)
    return payload


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
        balance = db.user_total_balance_sats(user.id, network)
        db.set_leaderboard_opt_in(
            user.id, network, body.display_name.strip(), True, balance
        )
        db.add_audit(
            "LEADERBOARD_OPT_IN",
            user_id=user.id,
            details=f"network={network}",
        )
    else:
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
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    entry = db.get_leaderboard_entry(user.id, body.network)
    if not entry or not entry["opted_in"]:
        raise HTTPException(status_code=400, detail="Leaderboard opt-in required")

    if not db.update_leaderboard_balance(user.id, body.network, body.balance_sats):
        raise HTTPException(status_code=400, detail="Leaderboard entry not found")

    _cache.clear()
    return {
        "network": body.network,
        "balance_sats": body.balance_sats,
        "rank": db.get_leaderboard_rank(user.id, body.network),
    }

"""Rate limiting for sensitive API endpoints."""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from pathlib import Path
from threading import Lock

from fastapi import HTTPException, Request

_lock = Lock()
_attempts: dict[str, list[float]] = defaultdict(list)

DEFAULT_LIMIT = 10
DEFAULT_WINDOW = 60

SCOPE_LIMITS: dict[str, tuple[int, int]] = {
    "login": (10, 60),
    "register": (5, 60),
    "wallet_unlock": (5, 300),
    "send": (10, 60),
    "swap_quote": (60, 60),
    "swap_execute": (20, 60),
    "leaderboard_get": (120, 60),
    "leaderboard_update": (6, 60),
    "leaderboard_remote_register": (20, 60),
    "leaderboard_remote_update": (6, 60),
    "leaderboard_remote_opt_out": (10, 60),
}


def _rate_limit_file() -> Path:
    raw = os.getenv("RATE_LIMIT_FILE", "./data/rate_limits.json").strip()
    return Path(raw)


def _load_file_attempts() -> dict[str, list[float]]:
    path = _rate_limit_file()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: [float(t) for t in v] for k, v in data.items()}
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return {}


def _save_file_attempts(data: dict[str, list[float]]) -> None:
    path = _rate_limit_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _client_key(request: Request, scope: str) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    else:
        ip = "unknown"
    return f"{scope}:{ip}"


def _prune(bucket: list[float], now: float, window_seconds: int) -> list[float]:
    return [t for t in bucket if now - t < window_seconds]


def check_rate_limit(
    request: Request,
    scope: str,
    *,
    limit: int | None = None,
    window_seconds: int | None = None,
) -> None:
    scoped = SCOPE_LIMITS.get(scope)
    if limit is None:
        limit = scoped[0] if scoped else DEFAULT_LIMIT
    if window_seconds is None:
        window_seconds = scoped[1] if scoped else DEFAULT_WINDOW

    key = _client_key(request, scope)
    now = time.time()
    with _lock:
        if os.getenv("RATE_LIMIT_BACKEND", "memory").strip().lower() == "file":
            store = _load_file_attempts()
            bucket = _prune(store.get(key, []), now, window_seconds)
        else:
            bucket = _prune(_attempts[key], now, window_seconds)

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many attempts — try again later",
            )

        bucket.append(now)
        if os.getenv("RATE_LIMIT_BACKEND", "memory").strip().lower() == "file":
            store[key] = bucket
            _save_file_attempts(store)
        else:
            _attempts[key] = bucket

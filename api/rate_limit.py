"""Simple in-memory rate limiting for auth endpoints."""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request

_lock = Lock()
_attempts: dict[str, list[float]] = defaultdict(list)

DEFAULT_LIMIT = 10
DEFAULT_WINDOW = 60


def _client_key(request: Request, scope: str) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    else:
        ip = "unknown"
    return f"{scope}:{ip}"


def check_rate_limit(
    request: Request,
    scope: str,
    *,
    limit: int = DEFAULT_LIMIT,
    window_seconds: int = DEFAULT_WINDOW,
) -> None:
    key = _client_key(request, scope)
    now = time.time()
    with _lock:
        bucket = [t for t in _attempts[key] if now - t < window_seconds]
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many attempts — try again later",
            )
        bucket.append(now)
        _attempts[key] = bucket

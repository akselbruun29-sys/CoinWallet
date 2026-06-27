"""Security middleware for the local wallet API sidecar."""
from __future__ import annotations

import os
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api.auth import (
    SESSION_COOKIE,
    set_session_cookie,
    touch_session_token,
    verify_session_token,
)
from src.wallet.vault import touch_unlock

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "[::1]", "::1"})
_DEFAULT_CORS_ORIGINS = frozenset(
    {
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    }
)
_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _localhost_only_enabled() -> bool:
    if os.getenv("ALLOW_REMOTE_API_HOST", "").lower() in ("true", "1", "yes"):
        return False
    if os.getenv("LOCALHOST_ONLY", "").lower() in ("false", "0", "no"):
        return False
    return True


def _strict_localhost_mode() -> bool:
    if os.getenv("STRICT_SECRETS", "").lower() in ("true", "1", "yes"):
        return True
    return _localhost_only_enabled()


def _host_is_local(host: str) -> bool:
    if not host:
        return False
    # Strip port: localhost:8002 → localhost
    name = host.split(":")[0].strip().lower()
    if name.startswith("[") and name.endswith("]"):
        name = name[1:-1]
    return name in _LOCAL_HOSTS


def _client_is_local(request: Request) -> bool:
    if not request.client:
        return True
    host = request.client.host
    return host in ("127.0.0.1", "::1", "localhost")


class LocalhostOnlyMiddleware(BaseHTTPMiddleware):
    """Reject requests that do not target a loopback Host or originate remotely."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not _localhost_only_enabled():
            return await call_next(request)

        host = request.headers.get("host", "").strip()
        if _strict_localhost_mode() and not host:
            return JSONResponse(
                status_code=403,
                content={"detail": "Missing Host header"},
            )
        if host and not _host_is_local(host):
            return JSONResponse(
                status_code=403,
                content={"detail": "API is bound to localhost — invalid Host header"},
            )

        forwarded = request.headers.get("x-forwarded-host", "")
        if forwarded:
            first = forwarded.split(",")[0].strip()
            if first and not _host_is_local(first):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid X-Forwarded-Host for local API"},
                )

        strict_client = os.getenv("STRICT_SECRETS", "").lower() in ("true", "1", "yes")
        if strict_client and not _client_is_local(request):
            return JSONResponse(
                status_code=403,
                content={"detail": "API accepts loopback clients only"},
            )

        return await call_next(request)


def _allowed_origins() -> frozenset[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return _DEFAULT_CORS_ORIGINS
    return frozenset(o.strip().rstrip("/") for o in raw.split(",") if o.strip())


def _request_origin(request: Request) -> str:
    origin = (request.headers.get("origin") or "").strip().rstrip("/")
    if origin:
        return origin
    referer = (request.headers.get("referer") or "").strip()
    if not referer:
        return ""
    from urllib.parse import urlparse

    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _session_token_from_request(request: Request) -> Optional[str]:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        return token
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


class CsrfOriginMiddleware(BaseHTTPMiddleware):
    """
    Cookie-authenticated mutating requests must include a matching Origin/Referer.

    Bearer-token clients (desktop SPA) are exempt — SameSite=Lax on cookies plus
    this check covers browser cookie sessions without double-submit tokens.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in _MUTATING_METHODS:
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            return await call_next(request)

        if not request.cookies.get(SESSION_COOKIE):
            return await call_next(request)

        origin = _request_origin(request)
        if not origin or origin not in _allowed_origins():
            return JSONResponse(
                status_code=403,
                content={"detail": "Cross-origin request blocked — invalid Origin"},
            )
        return await call_next(request)


class SessionActivityMiddleware(BaseHTTPMiddleware):
    """Extend session idle timer and rotate token payload on authenticated activity."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        token = _session_token_from_request(request)
        refreshed = touch_session_token(token) if token else None
        response = await call_next(request)
        if refreshed and refreshed != token:
            if request.cookies.get(SESSION_COOKIE):
                set_session_cookie(response, refreshed)
            else:
                response.headers["X-Session-Token"] = refreshed
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers to every API response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'",
        )
        return response


def _user_id_from_request(request: Request) -> Optional[int]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
    if not token:
        return None
    session = verify_session_token(token)
    if not session:
        return None
    return int(session["id"])


class WalletActivityMiddleware(BaseHTTPMiddleware):
    """Extend wallet unlock idle timer on authenticated API activity."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        user_id = _user_id_from_request(request)
        if user_id is not None:
            touch_unlock(user_id)
        return await call_next(request)

"""FastAPI control plane for the Bitcoin wallet platform."""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.admin import router as admin_router
from api.events import router as events_router
from api.security import router as security_router
from api.auth import (
    AuthUser,
    SESSION_IDLE_SECONDS,
    clear_session_cookie,
    create_session_token,
    get_any_authenticated_user,
    get_current_user,
    get_db,
    hash_password,
    require_admin,
    set_session_cookie,
    verify_password,
)
from api.rate_limit import check_rate_limit
from api.leaderboard import router as leaderboard_router
from api.remote_leaderboard import router as remote_leaderboard_router
from api.middleware import (
    CsrfOriginMiddleware,
    LocalhostOnlyMiddleware,
    SecurityHeadersMiddleware,
    SessionActivityMiddleware,
    WalletActivityMiddleware,
)
from api.swap import router as swap_router
from api.network import router as network_router
from api.wallet import router as wallet_router
from src.config import validate_secrets
from src.database import WalletDatabase
from src.wallet.core import WalletService
from src.wallet.vault import configure_unlock_ttl, lock_user

load_dotenv()

validate_secrets()


def _apply_wallet_unlock_ttl(db: WalletDatabase) -> None:
    raw = (db.get_setting("wallet_unlock_ttl") or "").strip()
    if raw:
        try:
            configure_unlock_ttl(int(raw))
        except ValueError:
            pass


_db_bootstrap = WalletDatabase()
_apply_wallet_unlock_ttl(_db_bootstrap)
_DB_PATH = _db_bootstrap.db_path


@asynccontextmanager
async def _lifespan(_app):
    yield
    from src.db_at_rest import seal_db_path

    seal_db_path(_DB_PATH)


_DEFAULT_CORS_ORIGINS = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return _DEFAULT_CORS_ORIGINS
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS cannot include '*' when allow_credentials is enabled"
        )
    return origins


app = FastAPI(title="Wallet Vault API", version="0.2.0", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LocalhostOnlyMiddleware)
app.add_middleware(CsrfOriginMiddleware)
app.add_middleware(SessionActivityMiddleware)
app.add_middleware(WalletActivityMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(wallet_router)
app.include_router(network_router)
app.include_router(swap_router)
app.include_router(leaderboard_router)
app.include_router(remote_leaderboard_router)
app.include_router(admin_router)
app.include_router(events_router)
app.include_router(security_router)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=8)
    email: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


def _today_log_path() -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    return Path("logs") / f"wallet_{date_str}.log"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


@app.get("/api/health")
def health(db: WalletDatabase = Depends(get_db)):
    settings = db.get_system_settings()
    network = settings.get("network", "testnet")
    backend_ok = True
    backend_message = "ok"
    try:
        from src.wallet.backend import get_backend

        backend = get_backend(network, db)
        backend.tip_height()
    except Exception as exc:
        backend_ok = False
        backend_message = str(exc)
    return {
        "status": "ok" if backend_ok else "degraded",
        "app": "wallet-vault",
        "phase": 3,
        "backend_ok": backend_ok,
        "backend_message": backend_message,
        "network": network,
    }


@app.get("/api/auth/config")
def auth_config():
    return {
        "open_registration": os.getenv("OPEN_REGISTRATION", "false").lower() == "true",
        "auto_approve_users": os.getenv("AUTO_APPROVE_USERS", "true").lower() == "true",
        "session_idle_seconds": SESSION_IDLE_SECONDS,
        "session_max_age_days": 7,
        "csrf_model": "samesite_lax_plus_origin_check",
        "auth_primary": "bearer_token",
    }


@app.post("/api/auth/register")
def register(body: RegisterRequest, request: Request, db: WalletDatabase = Depends(get_db)):
    check_rate_limit(request, "register")
    if os.getenv("OPEN_REGISTRATION", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Registration is disabled")

    if db.get_user_by_username(body.username):
        raise HTTPException(status_code=409, detail="Username already exists")

    role = "user" if os.getenv("AUTO_APPROVE_USERS", "true").lower() == "true" else "pending"
    user_id = db.create_user(
        body.username,
        hash_password(body.password),
        role=role,
        email=body.email,
    )
    db.add_audit(
        "USER_REGISTERED",
        user_id=user_id,
        details=f"role={role}",
        ip=_client_ip(request),
    )
    return {"id": user_id, "username": body.username, "role": role}


@app.post("/api/auth/login")
def login(
    body: LoginRequest,
    response: Response,
    request: Request,
    db: WalletDatabase = Depends(get_db),
):
    check_rate_limit(request, "login")
    password_hash = db.get_user_password_hash(body.username)
    if not password_hash or not verify_password(body.password, password_hash):
        db.add_audit(
            "LOGIN_FAILED",
            details=f"username={body.username}",
            ip=_client_ip(request),
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user = db.get_user_by_username(body.username)
    if not user:
        db.add_audit(
            "LOGIN_FAILED",
            details=f"username={body.username}",
            ip=_client_ip(request),
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account disabled")

    lock_user(user["id"])
    token = create_session_token(user["id"], user["username"], user["role"])
    set_session_cookie(response, token)
    db.update_last_login(user["id"])
    db.add_audit("USER_LOGIN", user_id=user["id"], ip=_client_ip(request))

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "token": token,
    }


@app.post("/api/auth/logout")
def logout(
    response: Response,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    lock_user(user.id)
    clear_session_cookie(response)
    db.add_audit("USER_LOGOUT", user_id=user.id)
    return {"status": "logged_out"}


@app.get("/api/auth/me")
def me(user: AuthUser = Depends(get_any_authenticated_user), db: WalletDatabase = Depends(get_db)):
    full = db.get_user_by_id(user.id)
    return full


@app.post("/api/auth/change-password")
def change_password(
    body: ChangePasswordRequest,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    current_hash = db.get_user_password_hash(user.username)
    if not current_hash or not verify_password(body.current_password, current_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    db.change_password(user.id, hash_password(body.new_password))
    db.add_audit("PASSWORD_CHANGED", user_id=user.id)
    return {"status": "ok"}


@app.get("/api/status")
def status(user: AuthUser = Depends(get_current_user), db: WalletDatabase = Depends(get_db)):
    from api.security import wallet_security_status

    wallets = db.list_wallets(user.id)
    settings = db.get_system_settings()
    service = WalletService(db)
    synced = service.any_wallet_synced(user.id) if wallets else False
    security = wallet_security_status(user, db)
    return {
        "user": {"id": user.id, "username": user.username, "role": user.role},
        "wallets": wallets,
        "wallet_count": len(wallets),
        "network": settings.get("network", "testnet"),
        "tor_enabled": settings.get("tor_enabled", "false") == "true",
        "synced": synced,
        "wallet_security": security,
    }


@app.get("/api/logs")
def logs(
    tail: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    _: AuthUser = Depends(require_admin),
):
    log_path = _today_log_path()
    if not log_path.exists():
        return {"lines": [], "path": str(log_path)}

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()

    if level:
        level_upper = level.upper()
        lines = [ln for ln in lines if f" - {level_upper} - " in ln.upper()]

    if search:
        search_lower = search.lower()
        lines = [ln for ln in lines if search_lower in ln.lower()]

    return {"lines": lines[-tail:], "path": str(log_path)}


@app.get("/api/settings")
def settings(user: AuthUser = Depends(get_current_user), db: WalletDatabase = Depends(get_db)):
    all_settings = db.get_system_settings()
    if user.role == "admin":
        return all_settings
    return {
        "network": all_settings.get("network", "testnet"),
        "tor_enabled": all_settings.get("tor_enabled", "false"),
        "allow_mainnet": all_settings.get("allow_mainnet", "false"),
        "wallet_unlock_ttl": all_settings.get("wallet_unlock_ttl", "900"),
    }

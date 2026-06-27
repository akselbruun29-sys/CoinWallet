"""Admin API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import AuthUser, get_db, hash_password, require_admin
from src.database import WalletDatabase, USER_ROLES
from src.wallet.backend import get_backend
from src.wallet.vault import configure_unlock_ttl

router = APIRouter(prefix="/api/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=8)
    role: str = Field(default="user")
    email: Optional[str] = None


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UpdateSettingsRequest(BaseModel):
    network: Optional[str] = Field(default=None, pattern="^(testnet|signet|regtest|mainnet)$")
    backend_uri: Optional[str] = None
    backend_type: Optional[str] = Field(default=None, pattern="^(esplora|core)$")
    tor_enabled: Optional[bool] = None
    coordinator_uri: Optional[str] = None
    allow_mainnet: Optional[bool] = None
    mainnet_enable_acknowledged: Optional[bool] = None
    xmr_wallet_rpc_uri: Optional[str] = None
    wallet_unlock_ttl: Optional[int] = Field(default=None, ge=60, le=86_400)


@router.get("/users")
def list_users(
    _: AuthUser = Depends(require_admin),
    db: WalletDatabase = Depends(get_db),
):
    return db.list_users_with_stats()


@router.post("/users")
def create_user(
    body: CreateUserRequest,
    admin: AuthUser = Depends(require_admin),
    db: WalletDatabase = Depends(get_db),
):
    if body.role not in USER_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {USER_ROLES}")

    if db.get_user_by_username(body.username):
        raise HTTPException(status_code=409, detail="Username already exists")

    user_id = db.create_user(
        body.username,
        hash_password(body.password),
        role=body.role,
        email=body.email,
    )
    db.add_audit(
        "USER_CREATED",
        user_id=admin.id,
        details=f"created user_id={user_id} username={body.username} role={body.role}",
    )
    return db.get_user_by_id(user_id)


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    body: UpdateUserRequest,
    admin: AuthUser = Depends(require_admin),
    db: WalletDatabase = Depends(get_db),
):
    target = db.get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == admin.id:
        if body.is_active is False:
            raise HTTPException(status_code=400, detail="You cannot disable your own account")
        if body.role is not None and body.role != "admin":
            raise HTTPException(status_code=400, detail="You cannot demote your own admin role")

    if body.role is not None and body.role not in USER_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {USER_ROLES}")

    if (
        target["role"] == "admin"
        and body.role is not None
        and body.role != "admin"
        and db.count_admins() <= 1
    ):
        raise HTTPException(status_code=400, detail="Cannot demote the last admin")

    if target["role"] == "admin" and body.is_active is False and db.count_admins() <= 1:
        raise HTTPException(status_code=400, detail="Cannot disable the last admin")

    db.update_user(user_id, role=body.role, is_active=body.is_active)
    details = f"user_id={user_id}"
    if body.role is not None:
        details += f" role={body.role}"
    if body.is_active is not None:
        details += f" active={body.is_active}"
    db.add_audit("USER_UPDATED", user_id=admin.id, details=details)
    return db.get_user_by_id(user_id)


@router.get("/audit-log")
def audit_log(
    limit: int = 50,
    _: AuthUser = Depends(require_admin),
    db: WalletDatabase = Depends(get_db),
):
    return db.get_audit_log(limit=limit)


@router.get("/system")
def system_info(
    _: AuthUser = Depends(require_admin),
    db: WalletDatabase = Depends(get_db),
):
    settings = db.get_system_settings()
    network = settings.get("network", "testnet")
    height = 0
    peers = 0
    backend = get_backend(network, db)
    message = f"{backend.backend_name()} backend"
    try:
        height = backend.tip_height()
        peers = backend.peer_count()
    except Exception as exc:
        message = f"Backend unreachable: {exc}"
    return {
        "settings": settings,
        "node_height": height,
        "peer_count": peers,
        "backend": backend.backend_name(),
        "version": "0.2.0-phase2",
        "message": message,
    }


@router.patch("/settings")
def update_settings(
    body: UpdateSettingsRequest,
    admin: AuthUser = Depends(require_admin),
    db: WalletDatabase = Depends(get_db),
):
    if body.network is not None:
        if body.network == "mainnet":
            allowed = db.get_setting("allow_mainnet", "false").lower() == "true"
            if not allowed:
                raise HTTPException(
                    status_code=400,
                    detail="Enable allow_mainnet before setting default network to mainnet",
                )
        db.set_setting("network", body.network)
    if body.backend_uri is not None:
        db.set_setting("backend_uri", body.backend_uri.strip())
    if body.backend_type is not None:
        db.set_setting("backend_type", body.backend_type)
    if body.tor_enabled is not None:
        db.set_setting("tor_enabled", "true" if body.tor_enabled else "false")
    if body.coordinator_uri is not None:
        db.set_setting("coordinator_uri", body.coordinator_uri.strip())
    if body.allow_mainnet is not None:
        if body.allow_mainnet and not body.mainnet_enable_acknowledged:
            raise HTTPException(
                status_code=400,
                detail="Enable mainnet requires mainnet_enable_acknowledged=true",
            )
        was_allowed = db.get_setting("allow_mainnet", "false").lower() == "true"
        db.set_setting("allow_mainnet", "true" if body.allow_mainnet else "false")
        if body.allow_mainnet and not was_allowed:
            db.add_audit(
                "MAINNET_ENABLED",
                user_id=admin.id,
                details="admin enabled allow_mainnet",
            )
        if not body.allow_mainnet:
            db.set_setting("mainnet_enabled_at", "")
        elif body.mainnet_enable_acknowledged:
            from datetime import datetime, timezone

            db.set_setting(
                "mainnet_enabled_at",
                datetime.now(timezone.utc).isoformat(),
            )
    if body.xmr_wallet_rpc_uri is not None:
        db.set_setting("xmr_wallet_rpc_uri", body.xmr_wallet_rpc_uri.strip())
    if body.wallet_unlock_ttl is not None:
        configure_unlock_ttl(body.wallet_unlock_ttl)
        db.set_setting("wallet_unlock_ttl", str(body.wallet_unlock_ttl))

    db.add_audit("SETTINGS_UPDATED", user_id=admin.id, details="system settings changed")
    return db.get_system_settings()

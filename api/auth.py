"""Authentication helpers for the wallet API."""
import os
import secrets
import time
from dataclasses import dataclass
from typing import Optional

import bcrypt
from fastapi import Cookie, Depends, Header, HTTPException, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.database import WalletDatabase

SESSION_COOKIE = "wv_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days
SESSION_IDLE_SECONDS = int(os.getenv("SESSION_IDLE_SECONDS", "3600"))  # 1 hour


@dataclass
class AuthUser:
    id: int
    username: str
    role: str
    is_active: bool


def _serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("SESSION_SECRET", "change-me-in-production")
    return URLSafeTimedSerializer(secret, salt="wallet-vault")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_session_token(user_id: int, username: str, role: str) -> str:
    now = time.time()
    return _serializer().dumps(
        {
            "id": user_id,
            "user": username,
            "role": role,
            "iat": now,
            "last": now,
            "sid": secrets.token_hex(16),
        }
    )


def verify_session_token(token: str) -> Optional[dict]:
    try:
        data = _serializer().loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None

    last = float(data.get("last", data.get("iat", 0)))
    if time.time() - last > SESSION_IDLE_SECONDS:
        return None
    return data


def touch_session_token(token: str) -> Optional[str]:
    data = verify_session_token(token)
    if not data:
        return None
    data["last"] = time.time()
    return _serializer().dumps(data)


def set_session_cookie(response: Response, token: str) -> None:
    secure = os.getenv("SECURE_COOKIES", "false").lower() in ("true", "1", "yes")
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=SESSION_MAX_AGE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, path="/")


def _resolve_user(session_data: dict, db: WalletDatabase) -> AuthUser:
    user = db.get_user_by_id(session_data["id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account disabled")
    return AuthUser(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        is_active=user["is_active"],
    )


def get_db() -> WalletDatabase:
    return WalletDatabase()


def get_any_authenticated_user(
    authorization: Optional[str] = Header(None),
    session: Optional[str] = Cookie(None, alias=SESSION_COOKIE),
    db: WalletDatabase = Depends(get_db),
) -> AuthUser:
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif session:
        token = session

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = verify_session_token(token)
    if not session_data or "id" not in session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return _resolve_user(session_data, db)


def get_current_user(
    user: AuthUser = Depends(get_any_authenticated_user),
) -> AuthUser:
    if user.role == "pending":
        raise HTTPException(status_code=403, detail="Account pending approval")
    return user


def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

"""Authentication helpers for the wallet API."""
import os
from dataclasses import dataclass
from typing import Optional

import bcrypt
from fastapi import Cookie, Depends, Header, HTTPException, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.database import WalletDatabase

SESSION_COOKIE = "wv_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


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
    return _serializer().dumps({"id": user_id, "user": username, "role": role})


def verify_session_token(token: str) -> Optional[dict]:
    try:
        return _serializer().loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
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

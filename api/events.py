"""WebSocket event hub for live wallet updates."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.auth import SESSION_COOKIE, verify_session_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ws", tags=["events"])

_AUTH_TIMEOUT_SECONDS = 10


class EventHub:
    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = {}

    def register(self, user_id: int, websocket: WebSocket) -> None:
        self._connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id, [])
        if websocket in sockets:
            sockets.remove(websocket)
        if not sockets and user_id in self._connections:
            del self._connections[user_id]

    async def send_user(self, user_id: int, payload: dict[str, Any]) -> None:
        for websocket in list(self._connections.get(user_id, [])):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(user_id, websocket)


hub = EventHub()


async def _session_from_auth_message(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if data.get("type") != "auth":
        return None
    token = str(data.get("token", "")).strip()
    if not token:
        return None
    session = verify_session_token(token)
    return session if session else None


async def _authenticate_websocket(websocket: WebSocket) -> int | None:
    await websocket.accept()

    cookie_token = websocket.cookies.get(SESSION_COOKIE)
    if cookie_token:
        session = verify_session_token(cookie_token)
        if session:
            await websocket.send_json({"type": "auth_ok"})
            return int(session["id"])

    try:
        raw = await asyncio.wait_for(
            websocket.receive_text(), timeout=_AUTH_TIMEOUT_SECONDS
        )
    except TimeoutError:
        await websocket.close(code=4401, reason="Auth timeout")
        return None

    session = await _session_from_auth_message(raw)
    if not session:
        await websocket.close(code=4401, reason="Auth failed")
        return None

    await websocket.send_json({"type": "auth_ok"})
    return int(session["id"])


@router.websocket("/events")
async def wallet_events(websocket: WebSocket) -> None:
    user_id = await _authenticate_websocket(websocket)
    if user_id is None:
        return

    hub.register(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(user_id, websocket)


def publish_wallet_event(user_id: int, event: str, **data: Any) -> None:
    payload = {"event": event, **data}

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(hub.send_user(user_id, payload))
    except RuntimeError:
        logger.debug("No event loop for wallet event %s", event)

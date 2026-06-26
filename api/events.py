"""WebSocket event hub for live wallet updates."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from api.auth import verify_session_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ws", tags=["events"])


class EventHub:
    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
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


@router.websocket("/events")
async def wallet_events(websocket: WebSocket, token: str = Query(...)) -> None:
    session = verify_session_token(token)
    if not session:
        await websocket.close(code=4401)
        return

    user_id = int(session["id"])
    await hub.connect(user_id, websocket)
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

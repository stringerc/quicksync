"""Push last chat summary to HUD WebSocket clients."""

from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, WebSocket


async def broadcast_hud(fastapi_app: FastAPI, payload: dict[str, Any]) -> None:
    fastapi_app.state.hud_last = payload
    dead: list[WebSocket] = []
    msg = json.dumps(payload)
    for ws in getattr(fastapi_app.state, "hud_clients", []):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in fastapi_app.state.hud_clients:
            fastapi_app.state.hud_clients.remove(ws)

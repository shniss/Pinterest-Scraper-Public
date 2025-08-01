"""
WebSocket routes for the Pinterest Agent Platform API.

This module handles all WebSocket connections for real-time
communication between the backend and frontend.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.messaging.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/ws/{pid}")
async def ws_prompt(ws: WebSocket, pid: str):
    """
    Connects to the websocket for a given prompt id
    """
    print(f"WebSocket connection request for PID: {pid}")
    await ws_manager.connect(pid, ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(pid, ws)

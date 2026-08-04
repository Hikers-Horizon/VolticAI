"""
WebSocket endpoints for real-time quotes and notifications
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Set
import asyncio
import json
from loguru import logger
from app.services.market_data import market_service

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []
        self.subscriptions: dict = {}  # ws -> set of symbols

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)
        self.subscriptions[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)
        self.subscriptions.pop(websocket, None)

    async def send(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)


manager = ConnectionManager()


@router.websocket("/quotes")
async def ws_quotes(websocket: WebSocket):
    """
    Real-time quote stream.
    Client sends: {"action": "subscribe", "symbols": ["RELIANCE", "TCS"]}
    Server pushes quote updates every second for subscribed symbols.
    """
    await manager.connect(websocket)
    try:
        # Start background pusher
        async def pusher():
            while True:
                symbols = list(manager.subscriptions.get(websocket, set()))
                if symbols:
                    try:
                        quotes = await market_service.get_quotes(symbols)
                        await manager.send(websocket, {
                            "type": "quotes",
                            "data": quotes,
                        })
                    except Exception as e:
                        logger.warning(f"WS quote push error: {e}")
                await asyncio.sleep(1)

        push_task = asyncio.create_task(pusher())

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send(websocket, {"type": "error", "message": "Invalid JSON"})
                continue

            action = msg.get("action")
            if action == "subscribe":
                syms = [s.upper() for s in msg.get("symbols", [])]
                manager.subscriptions[websocket].update(syms)
                await manager.send(websocket, {
                    "type": "subscribed",
                    "symbols": list(manager.subscriptions[websocket]),
                })
            elif action == "unsubscribe":
                syms = {s.upper() for s in msg.get("symbols", [])}
                manager.subscriptions[websocket] -= syms
                await manager.send(websocket, {
                    "type": "unsubscribed",
                    "symbols": list(manager.subscriptions[websocket]),
                })
            elif action == "ping":
                await manager.send(websocket, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS error: {e}")
        manager.disconnect(websocket)
    finally:
        push_task.cancel() if "push_task" in dir() else None


@router.websocket("/notifications")
async def ws_notifications(websocket: WebSocket):
    """Push trade alerts, signal updates, SL/target hits."""
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Notification channel ready",
        })
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw) if raw else {}
            if msg.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

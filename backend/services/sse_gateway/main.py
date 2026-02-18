"""SSE Gateway — subscribes to task-updates topic and streams events to connected clients."""

from __future__ import annotations

import asyncio
import json
import logging

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic_settings import BaseSettings

from connections import ConnectionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    BETTER_AUTH_URL: str = "http://todo-app-frontend:3000"
    model_config = {"env_file": ".env"}


settings = Settings()
app = FastAPI(title="SSE Gateway", version="1.0.0")
manager = ConnectionManager()


# --- Dapr Subscription (T030.1) ---


@app.get("/dapr/subscribe")
async def dapr_subscribe():
    """Return Dapr programmatic subscription for task-updates topic."""
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-updates",
            "route": "/events/task-updates",
        },
    ]


# --- Event Handler (T030.2) ---


@app.post("/events/task-updates")
async def handle_task_update(request: Request):
    """Handle task-updates events from Dapr pub/sub.

    Extracts user_id from event data and broadcasts to all connected SSE clients.
    """
    try:
        envelope = await request.json()
        data = envelope.get("data", {})
        user_id = data.get("user_id")

        if user_id:
            await manager.broadcast(user_id, data)
            logger.info(
                "Broadcast event",
                extra={"user_id": user_id, "change_type": data.get("change_type")},
            )
    except Exception:
        logger.exception("Failed to process task-update event")

    return {"status": "SUCCESS"}


# --- SSE Stream Endpoint (T030.3) ---


@app.get("/stream/tasks")
async def stream_tasks(request: Request, token: str = ""):
    """SSE endpoint for real-time task updates.

    Validates Bearer token (from Authorization header or ?token= query param,
    since EventSource API does not support custom headers).
    Registers connection and streams events as text/event-stream.
    Sends heartbeat ping every 30 seconds to keep connection alive.
    """
    # Accept token from Authorization header OR ?token= query param
    # (EventSource in browsers cannot set Authorization headers)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")

    if not token:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Missing Bearer token"})

    user_id = await _validate_token(token)
    if not user_id:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    # Register SSE connection
    queue = manager.connect(user_id)

    async def event_generator():
        try:
            while True:
                try:
                    # Wait for event with 30s timeout (heartbeat interval)
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"event: sync.task-changed\ndata: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield ": ping\n\n"
                except asyncio.CancelledError:
                    break
        finally:
            manager.disconnect(user_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _validate_token(token: str) -> str | None:
    """Validate Bearer token via Better Auth session endpoint."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.BETTER_AUTH_URL}/api/auth/get-session",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("user", {}).get("id")
    except Exception:
        logger.warning("Token validation failed", exc_info=True)
    return None


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "connections": manager.connection_count,
        "users": manager.user_count,
    }

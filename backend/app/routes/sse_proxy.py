"""SSE proxy route — forwards /api/stream/tasks to the SSE gateway via Dapr service invocation.

The SSE gateway maintains in-memory connection registries and subscribes to
task-updates topic. The backend acts as the auth-aware entry point that proxies
the streaming connection through to the SSE gateway.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.dependencies import get_current_user_from_request

logger = logging.getLogger(__name__)

router = APIRouter(tags=["SSE Proxy"])

DAPR_HTTP_PORT = 3500
SSE_GATEWAY_APP_ID = "sse-gateway"
# Dapr service invocation URL for SSE gateway /stream/tasks endpoint
SSE_GATEWAY_STREAM_URL = (
    f"http://localhost:{DAPR_HTTP_PORT}/v1.0/invoke/{SSE_GATEWAY_APP_ID}/method/stream/tasks"
)


@router.get("/api/stream/tasks")
async def proxy_sse_stream(request: Request):
    """Proxy SSE stream from SSE gateway.

    Validates the user's Bearer token (from Authorization header or ?token= query param),
    then proxies the streaming SSE connection to the SSE gateway via Dapr service invocation.
    The gateway performs its own token validation against the auth service.
    """
    # Extract token from Authorization header or query param
    token = request.query_params.get("token", "")
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")

    if not token:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Missing Bearer token"})

    # Validate token to get user_id (fail-fast before opening SSE connection)
    user_id = await get_current_user_from_request(request, token)
    if not user_id:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    # Proxy the SSE connection to the SSE gateway
    # Pass token as query param since Dapr service invocation rewrites the request
    gateway_url = f"{SSE_GATEWAY_STREAM_URL}?token={token}"

    async def event_generator():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", gateway_url) as response:
                    if response.status_code != 200:
                        logger.error(
                            "SSE gateway returned non-200",
                            extra={"status": response.status_code, "user_id": user_id},
                        )
                        return
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception:
            logger.warning(
                "SSE proxy connection ended",
                extra={"user_id": user_id},
                exc_info=False,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

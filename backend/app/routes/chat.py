"""
Chat routes — ChatKit endpoint, simple chat, and conversation management.
"""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlmodel import select

from app.chat.server import TodoChatKitServer
from app.chat.store import DatabaseChatKitStore
from app.config import settings
from app.database import async_session
from app.dependencies import bearer_scheme, get_current_user
from app.models import Conversation

router = APIRouter(tags=["Chat"])
logger = logging.getLogger(__name__)

_SIMPLE_CHAT_SYSTEM = """\
You are a task management assistant. Help users manage their todo list through
natural conversation. You can discuss adding, listing, completing, updating, and
deleting tasks. Stay focused on task management. For off-topic questions, politely
redirect the user to ask about their tasks instead.
"""

# Singleton instances — created once, shared across requests
_store = DatabaseChatKitStore()
_server = TodoChatKitServer(store=_store)


@router.post("/chatkit")
async def chatkit_handler(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_id: str = Depends(get_current_user),
):
    """ChatKit unified endpoint — handles all ChatKit client-server communication."""
    body = await request.body()

    context = {
        "user_id": user_id,
        "auth_token": credentials.credentials,
    }

    result = await _server.process(body, context)

    from chatkit.server import StreamingResult

    if isinstance(result, StreamingResult):
        return StreamingResponse(
            result,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        return JSONResponse(content=json.loads(result.json), media_type="application/json")


# ---------------------------------------------------------------------------
# Simple chat endpoint — direct OpenAI call, no MCP required
# ---------------------------------------------------------------------------


class SimpleChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


@router.post("/api/chat")
async def simple_chat(
    req: SimpleChatRequest,
    user_id: str = Depends(get_current_user),
):
    """Simple chat endpoint — calls OpenAI directly without MCP tools."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="Chat service not configured (missing OPENAI_API_KEY)")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL or None,
    )
    messages = [
        {"role": "system", "content": _SIMPLE_CHAT_SYSTEM},
        {"role": "user", "content": req.message},
    ]

    # Try configured model first, fall back to gpt-4o-mini if it fails
    models_to_try = [settings.OPENAI_MODEL]
    if settings.OPENAI_MODEL != "gpt-4o-mini":
        models_to_try.append("gpt-4o-mini")

    last_exc: Exception | None = None
    for model in models_to_try:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1024,
            )
            return {
                "response": response.choices[0].message.content,
                "conversation_id": req.conversation_id or str(uuid.uuid4()),
            }
        except Exception as exc:
            logger.error("Chat model %s failed: %s", model, exc)
            last_exc = exc

    raise HTTPException(status_code=500, detail=f"Chat error: {last_exc}")


# ---------------------------------------------------------------------------
# Conversation REST endpoints (Phase 9 — US7)
# ---------------------------------------------------------------------------


@router.get("/api/conversations")
async def list_conversations(
    user_id: str = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    after: str | None = Query(default=None),
):
    """List the authenticated user's conversations, newest first."""
    async with async_session() as db:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )

        if after:
            cursor_result = await db.execute(
                select(Conversation).where(Conversation.id == uuid.UUID(after))
            )
            cursor = cursor_result.scalar_one_or_none()
            if cursor:
                stmt = stmt.where(Conversation.updated_at < cursor.updated_at)

        stmt = stmt.limit(limit + 1)
        result = await db.execute(stmt)
        convs = list(result.scalars().all())

    has_more = len(convs) > limit
    if has_more:
        convs = convs[:limit]

    return {
        "data": [
            {
                "id": str(c.id),
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in convs
        ],
        "has_more": has_more,
        "after": str(convs[-1].id) if convs else None,
    }


@router.delete("/api/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user),
):
    """Delete a conversation and all its messages (cascade)."""
    async with async_session() as db:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == uuid.UUID(conversation_id),
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        await db.delete(conv)
        await db.commit()

    return None

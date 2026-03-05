"""
Chat routes — ChatKit endpoint, simple chat with function calling, and conversation management.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.chat.server import TodoChatKitServer
from app.chat.store import DatabaseChatKitStore
from app.config import settings
from app.database import async_session, get_session
from app.dependencies import bearer_scheme, get_current_user
from app.models import Conversation, Task

router = APIRouter(tags=["Chat"])
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — emphasises tool use
# ---------------------------------------------------------------------------

_SIMPLE_CHAT_SYSTEM = """\
You are a task management assistant with direct access to the user's task database.
You have tools to list, create, update, complete, and delete tasks.

CRITICAL RULES — follow these exactly:
1. When the user wants to ADD a task → call create_task() immediately, do not ask for confirmation.
2. When the user wants to SEE tasks → call list_tasks() immediately.
3. When the user wants to COMPLETE a task → call list_tasks() first if you don't have the task ID, then call complete_task().
4. When the user wants to DELETE a task → call list_tasks() first if you don't have the task ID, confirm once, then call delete_task().
5. When the user wants to UPDATE a task → call list_tasks() first if you don't have the task ID, then call update_task().
6. NEVER describe what you "would" do. Always call the appropriate tool and report the result.
7. After every tool call, summarise what was done in a friendly one-line message.
"""

# ---------------------------------------------------------------------------
# Tool schemas for OpenAI function calling
# ---------------------------------------------------------------------------

_CHAT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List the user's tasks, optionally filtered by status or a search term.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "pending", "completed"],
                        "description": "Filter by completion status. Defaults to 'all'.",
                    },
                    "search": {
                        "type": "string",
                        "description": "Search tasks by title or description.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title (required)."},
                    "description": {"type": "string", "description": "Optional longer description."},
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Task priority. Defaults to medium.",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Toggle a task's completion status (mark done or undo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "UUID of the task."},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update a task's title, description, or priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "UUID of the task."},
                    "title": {"type": "string", "description": "New title."},
                    "description": {"type": "string", "description": "New description."},
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "New priority.",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Permanently delete a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "UUID of the task to delete."},
                },
                "required": ["task_id"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executor — runs DB operations on behalf of the AI
# ---------------------------------------------------------------------------

async def _execute_tool(name: str, args: dict, user_id: str, db: AsyncSession) -> str:
    """Execute a tool call and return a plain-text result for the model."""
    try:
        if name == "list_tasks":
            stmt = select(Task).where(Task.user_id == user_id)
            status = args.get("status", "all")
            if status == "pending":
                stmt = stmt.where(Task.completed == False)  # noqa: E712
            elif status == "completed":
                stmt = stmt.where(Task.completed == True)  # noqa: E712
            search = args.get("search")
            if search:
                pattern = f"%{search}%"
                stmt = stmt.where(
                    or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
                )
            stmt = stmt.order_by(Task.created_at.desc())
            result = await db.execute(stmt)
            tasks = result.scalars().all()
            if not tasks:
                return "No tasks found."
            lines = []
            for t in tasks:
                icon = "✅" if t.completed else "⬜"
                line = f"{icon} {t.title} [id:{t.id}] (priority:{t.priority})"
                if t.description:
                    line += f" — {t.description[:80]}"
                lines.append(line)
            return "\n".join(lines)

        elif name == "create_task":
            title = args.get("title", "").strip()
            if not title:
                return "Error: task title cannot be empty."
            task = Task(
                title=title,
                description=args.get("description"),
                priority=args.get("priority", "medium"),
                user_id=user_id,
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            return f"Created task '{task.title}' with id:{task.id} (priority:{task.priority})."

        elif name == "complete_task":
            task_id = uuid.UUID(args["task_id"])
            result = await db.execute(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                return f"Task id:{args['task_id']} not found."
            task.completed = not task.completed
            task.updated_at = datetime.utcnow()
            await db.commit()
            status_word = "completed" if task.completed else "marked incomplete"
            return f"Task '{task.title}' {status_word}."

        elif name == "update_task":
            task_id = uuid.UUID(args["task_id"])
            result = await db.execute(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                return f"Task id:{args['task_id']} not found."
            if "title" in args:
                task.title = args["title"].strip()
            if "description" in args:
                task.description = args["description"]
            if "priority" in args:
                task.priority = args["priority"]
            task.updated_at = datetime.utcnow()
            await db.commit()
            return f"Updated task '{task.title}'."

        elif name == "delete_task":
            task_id = uuid.UUID(args["task_id"])
            result = await db.execute(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                return f"Task id:{args['task_id']} not found."
            title = task.title
            await db.delete(task)
            await db.commit()
            return f"Deleted task '{title}'."

        else:
            return f"Unknown tool: {name}"

    except Exception as exc:  # noqa: BLE001
        logger.error("Tool %s failed: %s", name, exc)
        return f"Error executing {name}: {exc}"

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


class HistoryMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class SimpleChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    history: list[HistoryMessage] = []  # previous turns for multi-turn context


@router.post("/api/chat")
async def simple_chat(
    req: SimpleChatRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Chat endpoint with OpenAI function calling — executes real DB operations."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="Chat service not configured (missing OPENAI_API_KEY)")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL or None,
    )

    # Build message history: system + last 10 prior turns + current user message
    messages: list[dict] = [{"role": "system", "content": _SIMPLE_CHAT_SYSTEM}]
    for h in req.history[-10:]:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": req.message})

    # Prefer configured model; fall back to gpt-4o-mini on the first failure
    primary_model = settings.OPENAI_MODEL
    fallback_model = "gpt-4o-mini" if primary_model != "gpt-4o-mini" else None
    active_model = primary_model

    # Tool-calling loop (max 5 rounds to prevent infinite loops)
    for _round in range(5):
        try:
            response = await client.chat.completions.create(
                model=active_model,
                messages=messages,
                tools=_CHAT_TOOLS,
                tool_choice="auto",
                max_tokens=1024,
            )
        except Exception as exc:
            if fallback_model and active_model != fallback_model:
                logger.warning("Model %s failed (%s), retrying with %s", active_model, exc, fallback_model)
                active_model = fallback_model
                continue
            logger.error("Chat completion failed (model=%s): %s", active_model, exc)
            raise HTTPException(status_code=500, detail=f"Chat error: {exc}")

        choice = response.choices[0]
        ai_msg = choice.message

        # Build the assistant dict to append to messages
        assistant_entry: dict = {"role": "assistant", "content": ai_msg.content or ""}
        if ai_msg.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in ai_msg.tool_calls
            ]
        messages.append(assistant_entry)

        # No tool calls → final answer
        if not ai_msg.tool_calls:
            return {
                "response": ai_msg.content or "Done.",
                "conversation_id": req.conversation_id or str(uuid.uuid4()),
            }

        # Execute every tool call and append results
        for tc in ai_msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            tool_result = await _execute_tool(tc.function.name, args, user_id, db)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

    # Shouldn't reach here, but return a safe fallback
    raise HTTPException(status_code=500, detail="Chat loop exceeded maximum rounds")


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

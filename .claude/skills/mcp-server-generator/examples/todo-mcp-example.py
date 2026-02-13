"""
Todo MCP Server — Complete Example
====================================
Production MCP server for the hackathon-todo application.
Exposes task CRUD operations as MCP tools for AI agent consumption.

Run:
  DATABASE_URL=postgresql://... AUTH_URL=http://localhost:3000/api/auth \
    python -m app.mcp.server

Test:
  mcp dev app/mcp/server.py

Register with Claude Code:
  claude mcp add --transport http todo-mcp http://localhost:8001/mcp
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.session import ServerSession
from mcp.types import CallToolResult, TextContent


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ["DATABASE_URL"]
AUTH_URL = os.environ.get("AUTH_URL", "http://localhost:3000/api/auth")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@dataclass
class AppContext:
    db_session_factory: sessionmaker
    http_client: httpx.AsyncClient


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    db_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    # Strip params incompatible with asyncpg
    for param in ["sslmode=require", "channel_binding=require"]:
        db_url = db_url.replace(f"?{param}", "").replace(f"&{param}", "")

    engine = create_async_engine(db_url, pool_size=5, max_overflow=10)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            yield AppContext(db_session_factory=factory, http_client=client)
        finally:
            await engine.dispose()


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = MCPServer("Todo MCP Server", lifespan=app_lifespan)

Ctx = Context[ServerSession, AppContext]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

async def validate_token(auth_token: str, ctx: Ctx) -> str:
    """Validate Bearer token via Better Auth, return user_id."""
    client = ctx.request_context.lifespan_context.http_client
    resp = await client.get(
        f"{AUTH_URL}/get-session",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    if resp.status_code != 200:
        raise ValueError("Invalid or expired authentication token")
    user_id = resp.json().get("user", {}).get("id")
    if not user_id:
        raise ValueError("Could not resolve user from session")
    return user_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data) -> CallToolResult:
    text = json.dumps(data, default=str) if not isinstance(data, str) else data
    return CallToolResult(content=[TextContent(type="text", text=text)])


def _err(msg: str) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=msg)], isError=True)


# ---------------------------------------------------------------------------
# Note: In production, import your SQLModel Task from app.models.
# Below we use raw SQL via SQLAlchemy text() for a self-contained example.
# Replace with proper model imports in real usage.
# ---------------------------------------------------------------------------

from sqlalchemy import text


# ---------------------------------------------------------------------------
# Tool: List Tasks
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_tasks(
    auth_token: str,
    ctx: Ctx,
    completed: bool | None = None,
) -> CallToolResult:
    """List all tasks for the authenticated user.

    Returns a JSON array of task objects sorted by creation date (newest first).
    Optionally filter by completion status.

    Args:
        auth_token: Bearer token from the user's session.
        completed: If provided, filter tasks by completion status (true/false).
    """
    user_id = await validate_token(auth_token, ctx)
    await ctx.info(f"Listing tasks for user {user_id}")

    query = "SELECT id, title, description, completed, created_at, updated_at FROM task WHERE user_id = :uid"
    params: dict = {"uid": user_id}

    if completed is not None:
        query += " AND completed = :completed"
        params["completed"] = completed

    query += " ORDER BY created_at DESC"

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        result = await db.execute(text(query), params)
        rows = result.mappings().all()

    tasks = [dict(row) for row in rows]
    return _ok(tasks)


# ---------------------------------------------------------------------------
# Tool: Get Task
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_task(
    task_id: str,
    auth_token: str,
    ctx: Ctx,
) -> CallToolResult:
    """Get a single task by ID.

    Returns the full task object including title, description, completed status,
    and timestamps. Returns an error if the task does not exist.

    Args:
        task_id: UUID of the task.
        auth_token: Bearer token from the user's session.
    """
    user_id = await validate_token(auth_token, ctx)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        result = await db.execute(
            text("SELECT id, title, description, completed, created_at, updated_at FROM task WHERE id = :id AND user_id = :uid"),
            {"id": task_id, "uid": user_id},
        )
        row = result.mappings().first()

    if not row:
        raise ValueError(f"Task {task_id} not found")

    return _ok(dict(row))


# ---------------------------------------------------------------------------
# Tool: Create Task
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_task(
    title: str,
    auth_token: str,
    ctx: Ctx,
    description: str = "",
) -> CallToolResult:
    """Create a new task for the authenticated user.

    The task starts as incomplete. Returns the created task object with its
    generated UUID.

    Args:
        title: Task title (1-255 characters, required).
        auth_token: Bearer token from the user's session.
        description: Optional task description (max 2000 characters).
    """
    title = title.strip()
    if not title or len(title) > 255:
        raise ValueError("Title must be 1-255 characters")
    if len(description) > 2000:
        raise ValueError("Description must be at most 2000 characters")

    user_id = await validate_token(auth_token, ctx)
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await ctx.info(f"Creating task '{title}' for user {user_id}")

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        await db.execute(
            text(
                "INSERT INTO task (id, title, description, completed, user_id, created_at, updated_at) "
                "VALUES (:id, :title, :desc, false, :uid, :now, :now)"
            ),
            {"id": task_id, "title": title, "desc": description.strip(), "uid": user_id, "now": now},
        )
        await db.commit()

    return _ok({
        "id": task_id,
        "title": title,
        "description": description.strip(),
        "completed": False,
        "created_at": now,
        "updated_at": now,
    })


# ---------------------------------------------------------------------------
# Tool: Update Task
# ---------------------------------------------------------------------------

@mcp.tool()
async def update_task(
    task_id: str,
    auth_token: str,
    ctx: Ctx,
    title: str | None = None,
    description: str | None = None,
) -> CallToolResult:
    """Update a task's title and/or description.

    Only provided fields are modified; omitted fields remain unchanged.
    Returns the updated task object.

    Args:
        task_id: UUID of the task to update.
        auth_token: Bearer token from the user's session.
        title: New title (1-255 characters, optional).
        description: New description (max 2000 characters, optional).
    """
    if title is not None:
        title = title.strip()
        if not title or len(title) > 255:
            raise ValueError("Title must be 1-255 characters")
    if description is not None and len(description) > 2000:
        raise ValueError("Description must be at most 2000 characters")

    user_id = await validate_token(auth_token, ctx)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        # Verify ownership
        result = await db.execute(
            text("SELECT id FROM task WHERE id = :id AND user_id = :uid"),
            {"id": task_id, "uid": user_id},
        )
        if not result.first():
            raise ValueError(f"Task {task_id} not found")

        sets = ["updated_at = :now"]
        params: dict = {"id": task_id, "uid": user_id, "now": datetime.now(timezone.utc).isoformat()}

        if title is not None:
            sets.append("title = :title")
            params["title"] = title
        if description is not None:
            sets.append("description = :desc")
            params["desc"] = description.strip()

        await db.execute(
            text(f"UPDATE task SET {', '.join(sets)} WHERE id = :id AND user_id = :uid"),
            params,
        )
        await db.commit()

        # Fetch updated row
        result = await db.execute(
            text("SELECT id, title, description, completed, created_at, updated_at FROM task WHERE id = :id"),
            {"id": task_id},
        )
        row = result.mappings().first()

    return _ok(dict(row))


# ---------------------------------------------------------------------------
# Tool: Toggle Task Completion
# ---------------------------------------------------------------------------

@mcp.tool()
async def toggle_task(
    task_id: str,
    auth_token: str,
    ctx: Ctx,
) -> CallToolResult:
    """Toggle a task's completion status.

    If the task is incomplete it becomes complete, and vice versa.
    Returns the updated task object.

    Args:
        task_id: UUID of the task.
        auth_token: Bearer token from the user's session.
    """
    user_id = await validate_token(auth_token, ctx)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        result = await db.execute(
            text("SELECT id, completed FROM task WHERE id = :id AND user_id = :uid"),
            {"id": task_id, "uid": user_id},
        )
        row = result.mappings().first()
        if not row:
            raise ValueError(f"Task {task_id} not found")

        new_status = not row["completed"]
        now = datetime.now(timezone.utc).isoformat()

        await db.execute(
            text("UPDATE task SET completed = :status, updated_at = :now WHERE id = :id AND user_id = :uid"),
            {"status": new_status, "now": now, "id": task_id, "uid": user_id},
        )
        await db.commit()

        result = await db.execute(
            text("SELECT id, title, description, completed, created_at, updated_at FROM task WHERE id = :id"),
            {"id": task_id},
        )
        updated = result.mappings().first()

    return _ok(dict(updated))


# ---------------------------------------------------------------------------
# Tool: Delete Task
# ---------------------------------------------------------------------------

@mcp.tool()
async def delete_task(
    task_id: str,
    auth_token: str,
    ctx: Ctx,
) -> CallToolResult:
    """Permanently delete a task.

    This action cannot be undone. Returns confirmation with the deleted task ID.

    Args:
        task_id: UUID of the task to delete.
        auth_token: Bearer token from the user's session.
    """
    user_id = await validate_token(auth_token, ctx)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        result = await db.execute(
            text("SELECT id FROM task WHERE id = :id AND user_id = :uid"),
            {"id": task_id, "uid": user_id},
        )
        if not result.first():
            raise ValueError(f"Task {task_id} not found")

        await db.execute(
            text("DELETE FROM task WHERE id = :id AND user_id = :uid"),
            {"id": task_id, "uid": user_id},
        )
        await db.commit()

    return _ok({"deleted": task_id})


# ---------------------------------------------------------------------------
# Tool: Task Summary (AI-optimized aggregate)
# ---------------------------------------------------------------------------

@mcp.tool()
async def task_summary(
    auth_token: str,
    ctx: Ctx,
) -> CallToolResult:
    """Get a summary of the user's tasks.

    Returns counts of total, completed, and pending tasks — useful for
    generating quick status reports without fetching all task details.

    Args:
        auth_token: Bearer token from the user's session.
    """
    user_id = await validate_token(auth_token, ctx)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        result = await db.execute(
            text(
                "SELECT "
                "  COUNT(*) as total, "
                "  COUNT(*) FILTER (WHERE completed = true) as done, "
                "  COUNT(*) FILTER (WHERE completed = false) as pending "
                "FROM task WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.mappings().first()

    return _ok({
        "total": row["total"],
        "completed": row["done"],
        "pending": row["pending"],
    })


# ---------------------------------------------------------------------------
# Resource: User Task Stats (read-only data for agent context)
# ---------------------------------------------------------------------------

@mcp.resource("todo://user/{user_id}/stats")
async def user_task_stats(user_id: str) -> str:
    """Read-only statistics about a user's tasks."""
    return json.dumps({
        "note": "Use the task_summary tool for live stats. This resource is a placeholder.",
        "user_id": user_id,
    })


# ---------------------------------------------------------------------------
# Prompt: Task Management Instructions
# ---------------------------------------------------------------------------

@mcp.prompt()
def manage_tasks_prompt(user_context: str = "") -> str:
    """Generate instructions for an AI assistant managing tasks.

    Args:
        user_context: Additional context about the user's request.
    """
    return (
        "You are a task management assistant. Help the user manage their todo list. "
        "Use the available MCP tools to list, create, update, toggle, and delete tasks. "
        "Always confirm destructive actions (delete) before executing. "
        "When listing tasks, group them by completion status. "
        f"{user_context}"
    )


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(
        transport=os.environ.get("MCP_TRANSPORT", "streamable-http"),
        host=os.environ.get("MCP_HOST", "0.0.0.0"),
        port=int(os.environ.get("MCP_PORT", "8001")),
    )

"""
MCP Server — Todo Task Operations
===================================
Standalone MCP server exposing task CRUD as tools for AI agent consumption.
Uses FastMCP with streamable-http transport on port 8001.

Run with uvicorn:
    cd backend && uvicorn mcp_server.server:app --host 0.0.0.0 --port 8001

Or as a module:
    cd backend && python -m mcp_server

Note: This package is named mcp_server/ (not mcp/) to avoid shadowing
the pip-installed 'mcp' SDK package.
"""

from __future__ import annotations

import json
import os
import ssl
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx
from dotenv import load_dotenv
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from mcp.server.fastmcp import Context, FastMCP

# ---------------------------------------------------------------------------
# Configuration — reads from .env, no dependency on app.config
# ---------------------------------------------------------------------------

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
BETTER_AUTH_URL = os.environ.get("BETTER_AUTH_URL", "http://localhost:3000")
MCP_PORT = int(os.environ.get("MCP_SERVER_PORT", "8001"))
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
AUTH_URL = f"{BETTER_AUTH_URL}/api/auth"


def _async_database_url(url: str) -> str:
    """Convert a PostgreSQL URL to asyncpg-compatible form."""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params.pop("sslmode", None)
    params.pop("channel_binding", None)
    return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))


ASYNC_DB_URL = _async_database_url(DATABASE_URL)

# ---------------------------------------------------------------------------
# Inline SQLModel — Task table (mirrors app.models.Task)
# ---------------------------------------------------------------------------
# We import SQLModel here so the MCP server is self-contained and doesn't
# need the full app package on sys.path.

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class Task(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Advanced fields
    priority: str = Field(default="medium")
    tags: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, server_default="[]"))
    due_date: datetime | None = Field(default=None)
    recurrence_pattern: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    reminder_minutes: int | None = Field(default=None)
    snoozed_until: datetime | None = Field(default=None)
    reminder_notified_at: datetime | None = Field(default=None)
    parent_task_id: uuid.UUID | None = Field(default=None, foreign_key="task.id")


# ---------------------------------------------------------------------------
# Lifespan — shared DB pool + HTTP client available to every tool via ctx
# ---------------------------------------------------------------------------


@dataclass
class AppContext:
    """Typed container for lifespan-managed dependencies."""

    db_session_factory: sessionmaker
    http_client: httpx.AsyncClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Create DB engine and HTTP client on startup; dispose on shutdown."""
    ssl_ctx = ssl.create_default_context()
    engine = create_async_engine(
        ASYNC_DB_URL,
        pool_size=5,
        max_overflow=10,
        connect_args={"ssl": ssl_ctx},
    )
    session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            yield AppContext(db_session_factory=session_factory, http_client=client)
        finally:
            await engine.dispose()


# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Todo MCP Server",
    lifespan=app_lifespan,
    host=MCP_HOST,
    port=MCP_PORT,
    streamable_http_path="/mcp",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def validate_token(auth_token: str, ctx: Context) -> str:
    """Validate a Bearer token via Better Auth and return user_id.

    Raises ValueError on invalid / expired tokens.
    """
    app_ctx: AppContext = ctx.request_context.lifespan_context
    resp = await app_ctx.http_client.get(
        f"{AUTH_URL}/get-session",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    if resp.status_code != 200:
        raise ValueError("Invalid or expired authentication token")

    data = resp.json()
    user_id = data.get("user", {}).get("id")
    if not user_id:
        raise ValueError("Could not resolve user from token")
    return user_id


def _json(data: dict | list) -> str:
    """Serialize to JSON string for tool return values."""
    return json.dumps(data, default=str)


def _task_dict(t: Task) -> dict:
    """Convert a Task row to a serialisable dict."""
    return {
        "id": str(t.id),
        "title": t.title,
        "description": t.description or "",
        "completed": t.completed,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "priority": t.priority,
        "tags": t.tags or [],
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "recurrence_pattern": t.recurrence_pattern,
        "reminder_minutes": t.reminder_minutes,
        "parent_task_id": str(t.parent_task_id) if t.parent_task_id else None,
    }


# ===================================================================
# MCP TOOLS (6)
# ===================================================================


# --- 1. add_task -------------------------------------------------------


@mcp.tool()
async def add_task(
    title: str,
    auth_token: str,
    description: str = "",
    priority: str = "medium",
    tags: list[str] | None = None,
    due_date: str | None = None,
    ctx: Context = None,
) -> str:
    """Create a new task for the authenticated user.

    Args:
        title: Task title (1-255 characters).
        auth_token: Bearer token from the user's session.
        description: Optional task description (max 2000 characters).
        priority: Task priority — high, medium, or low. Defaults to medium.
        tags: Optional list of tag strings (max 10, lowercase).
        due_date: Optional due date as ISO 8601 string.
    """
    title = title.strip()
    if not title or len(title) > 255:
        raise ValueError("Title must be 1-255 characters")
    if len(description) > 2000:
        raise ValueError("Description must be at most 2000 characters")
    if priority not in ("high", "medium", "low"):
        raise ValueError("Priority must be high, medium, or low")

    parsed_tags = [t.lower().strip() for t in (tags or [])][:10]
    parsed_due = None
    if due_date:
        parsed_due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

    user_id = await validate_token(auth_token, ctx)
    app_ctx: AppContext = ctx.request_context.lifespan_context

    async with app_ctx.db_session_factory() as db:
        task = Task(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            description=description or None,
            completed=False,
            priority=priority,
            tags=parsed_tags,
            due_date=parsed_due,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

    return _json(_task_dict(task))


# --- 2. list_tasks -----------------------------------------------------


@mcp.tool()
async def list_tasks(
    auth_token: str,
    completed: bool | None = None,
    priority: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    ctx: Context = None,
) -> str:
    """List all tasks for the authenticated user, optionally filtered.

    Args:
        auth_token: Bearer token from the user's session.
        completed: true=completed, false=pending, omit=all.
        priority: Filter by priority — high, medium, or low.
        tag: Filter by tag name.
        search: Search keyword in title and description.
    """
    from sqlalchemy import or_

    user_id = await validate_token(auth_token, ctx)
    app_ctx: AppContext = ctx.request_context.lifespan_context

    async with app_ctx.db_session_factory() as db:
        stmt = select(Task).where(Task.user_id == user_id)
        if completed is not None:
            stmt = stmt.where(Task.completed == completed)
        if priority and priority in ("high", "medium", "low"):
            stmt = stmt.where(Task.priority == priority)
        if tag:
            stmt = stmt.where(Task.tags.contains([tag]))
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
            )
        stmt = stmt.order_by(Task.created_at.desc())
        result = await db.execute(stmt)
        tasks = result.scalars().all()

    return _json([_task_dict(t) for t in tasks])


# --- 3. task_summary ---------------------------------------------------


@mcp.tool()
async def task_summary(
    auth_token: str,
    ctx: Context = None,
) -> str:
    """Get a summary of the user's tasks: total, completed, and pending.

    Args:
        auth_token: Bearer token from the user's session.
    """
    user_id = await validate_token(auth_token, ctx)
    app_ctx: AppContext = ctx.request_context.lifespan_context

    async with app_ctx.db_session_factory() as db:
        total = (
            await db.execute(
                select(func.count()).select_from(Task).where(Task.user_id == user_id)
            )
        ).scalar() or 0

        done = (
            await db.execute(
                select(func.count())
                .select_from(Task)
                .where(Task.user_id == user_id, Task.completed == True)  # noqa: E712
            )
        ).scalar() or 0

    return _json({"total": total, "completed": done, "pending": total - done})


# --- 4. complete_task --------------------------------------------------


@mcp.tool()
async def complete_task(
    task_id: str,
    auth_token: str,
    ctx: Context = None,
) -> str:
    """Toggle a task's completion status (done ↔ not done).

    Args:
        task_id: UUID of the task.
        auth_token: Bearer token from the user's session.
    """
    user_id = await validate_token(auth_token, ctx)
    app_ctx: AppContext = ctx.request_context.lifespan_context

    async with app_ctx.db_session_factory() as db:
        result = await db.execute(
            select(Task).where(
                Task.id == uuid.UUID(task_id), Task.user_id == user_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.completed = not task.completed
        task.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(task)

    return _json(_task_dict(task))


# --- 5. update_task ----------------------------------------------------


@mcp.tool()
async def update_task(
    task_id: str,
    auth_token: str,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    tags: list[str] | None = None,
    due_date: str | None = None,
    ctx: Context = None,
) -> str:
    """Update a task's fields.

    Args:
        task_id: UUID of the task.
        auth_token: Bearer token from the user's session.
        title: New title (1-255 chars). Omit to keep current.
        description: New description (max 2000 chars). Omit to keep current.
        priority: New priority — high, medium, or low. Omit to keep current.
        tags: New tags list. Omit to keep current.
        due_date: New due date as ISO 8601 string, or empty string to clear. Omit to keep current.
    """
    if title is not None:
        title = title.strip()
        if not title or len(title) > 255:
            raise ValueError("Title must be 1-255 characters")
    if description is not None and len(description) > 2000:
        raise ValueError("Description must be at most 2000 characters")
    if priority is not None and priority not in ("high", "medium", "low"):
        raise ValueError("Priority must be high, medium, or low")

    user_id = await validate_token(auth_token, ctx)
    app_ctx: AppContext = ctx.request_context.lifespan_context

    async with app_ctx.db_session_factory() as db:
        result = await db.execute(
            select(Task).where(
                Task.id == uuid.UUID(task_id), Task.user_id == user_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if tags is not None:
            task.tags = [t.lower().strip() for t in tags][:10]
        if due_date is not None:
            if due_date == "":
                task.due_date = None
            else:
                task.due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        task.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(task)

    return _json(_task_dict(task))


# --- 6. delete_task ----------------------------------------------------


@mcp.tool()
async def delete_task(
    task_id: str,
    auth_token: str,
    ctx: Context = None,
) -> str:
    """Permanently delete a task. Cannot be undone.

    Args:
        task_id: UUID of the task.
        auth_token: Bearer token from the user's session.
    """
    user_id = await validate_token(auth_token, ctx)
    app_ctx: AppContext = ctx.request_context.lifespan_context

    async with app_ctx.db_session_factory() as db:
        result = await db.execute(
            select(Task).where(
                Task.id == uuid.UUID(task_id), Task.user_id == user_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        await db.delete(task)
        await db.commit()

    return _json({"deleted": task_id})


# ===================================================================
# ASGI app — `uvicorn mcp_server.server:app --host 0.0.0.0 --port 8001`
# ===================================================================

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route


async def health(request):
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/mcp", app=mcp.streamable_http_app()),
    ],
)

# ===================================================================
# Direct entry point — `python -m mcp_server`
# ===================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)

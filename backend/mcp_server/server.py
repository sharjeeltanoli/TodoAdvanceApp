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

from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


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
    ctx: Context = None,
) -> str:
    """Create a new task for the authenticated user.

    Args:
        title: Task title (1-255 characters).
        auth_token: Bearer token from the user's session.
        description: Optional task description (max 2000 characters).
    """
    title = title.strip()
    if not title or len(title) > 255:
        raise ValueError("Title must be 1-255 characters")
    if len(description) > 2000:
        raise ValueError("Description must be at most 2000 characters")

    user_id = await validate_token(auth_token, ctx)
    app_ctx: AppContext = ctx.request_context.lifespan_context

    async with app_ctx.db_session_factory() as db:
        task = Task(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            description=description or None,
            completed=False,
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
    ctx: Context = None,
) -> str:
    """List all tasks for the authenticated user, optionally filtered.

    Args:
        auth_token: Bearer token from the user's session.
        completed: true=completed, false=pending, omit=all.
    """
    user_id = await validate_token(auth_token, ctx)
    app_ctx: AppContext = ctx.request_context.lifespan_context

    async with app_ctx.db_session_factory() as db:
        stmt = select(Task).where(Task.user_id == user_id)
        if completed is not None:
            stmt = stmt.where(Task.completed == completed)
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
    ctx: Context = None,
) -> str:
    """Update a task's title and/or description.

    Args:
        task_id: UUID of the task.
        auth_token: Bearer token from the user's session.
        title: New title (1-255 chars). Omit to keep current.
        description: New description (max 2000 chars). Omit to keep current.
    """
    if title is not None:
        title = title.strip()
        if not title or len(title) > 255:
            raise ValueError("Title must be 1-255 characters")
    if description is not None and len(description) > 2000:
        raise ValueError("Description must be at most 2000 characters")

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

app = mcp.streamable_http_app()

# ===================================================================
# Direct entry point — `python -m mcp_server`
# ===================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)

"""
MCP Server Template — Production-Ready Boilerplate
====================================================
Official MCP Python SDK (v1.2.0+)

Usage:
  1. Copy this file to backend/app/mcp/server.py
  2. Replace placeholders marked with {{PLACEHOLDER}}
  3. Register tools from tools/ modules
  4. Run: python -m app.mcp.server

Transport options:
  - streamable-http (default, recommended for web agents)
  - stdio (for CLI / local MCP clients)
  - sse (for browser clients)
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.session import ServerSession
from mcp.types import CallToolResult, TextContent


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_NAME = "{{SERVER_NAME}}"  # e.g. "Todo MCP Server"
DATABASE_URL = os.environ.get("DATABASE_URL", "")
AUTH_URL = os.environ.get("AUTH_URL", "http://localhost:3000/api/auth")
TRANSPORT = os.environ.get("MCP_TRANSPORT", "streamable-http")
HOST = os.environ.get("MCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("MCP_PORT", "8001"))


# ---------------------------------------------------------------------------
# Lifespan Context — shared resources available to all tools via ctx
# ---------------------------------------------------------------------------

@dataclass
class AppContext:
    """Typed container for lifespan-managed dependencies."""

    db_session_factory: sessionmaker
    http_client: httpx.AsyncClient


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    """Initialize DB pool and HTTP client; tear down on shutdown."""

    # Async SQLAlchemy engine (reuse project's DATABASE_URL)
    db_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url, pool_size=5, max_overflow=10)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            yield AppContext(db_session_factory=session_factory, http_client=client)
        finally:
            await engine.dispose()


# ---------------------------------------------------------------------------
# Server Instance
# ---------------------------------------------------------------------------

mcp = MCPServer(SERVER_NAME, lifespan=app_lifespan)


# ---------------------------------------------------------------------------
# Auth Helper — validates Bearer token against Better Auth
# ---------------------------------------------------------------------------

async def validate_token(
    auth_token: str,
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Validate a Bearer token and return user_id.

    Raises ValueError if the token is invalid or expired.
    """
    client = ctx.request_context.lifespan_context.http_client
    resp = await client.get(
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


# ---------------------------------------------------------------------------
# Helper — build success / error CallToolResult
# ---------------------------------------------------------------------------

def success_result(data: dict | list | str) -> CallToolResult:
    """Wrap data in a successful CallToolResult."""
    text = json.dumps(data) if not isinstance(data, str) else data
    return CallToolResult(content=[TextContent(type="text", text=text)])


def error_result(message: str) -> CallToolResult:
    """Wrap an error message in CallToolResult with isError flag."""
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        isError=True,
    )


# ---------------------------------------------------------------------------
# Tool Registration — import your domain tool modules here
# ---------------------------------------------------------------------------
# Example:
#   from app.mcp.tools import todos   # noqa: F401  (registers @mcp.tool via import)
#
# Each tool module should import `mcp` from this file:
#   from app.mcp.server import mcp, validate_token, success_result, error_result


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport=TRANSPORT, host=HOST, port=PORT)

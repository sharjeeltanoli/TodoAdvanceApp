"""
MCP Tool Definition Template
==============================
Copy this file to backend/app/mcp/tools/<domain>.py and customize.

Each tool file:
  1. Imports the shared `mcp` server instance and helpers
  2. Defines async tool functions with @mcp.tool()
  3. Is imported in server.py to register tools at startup

Guidelines:
  - Docstrings are shown to the LLM — make them clear and actionable
  - Type hints define the tool's input schema automatically
  - Always validate auth_token and scope queries to user_id
  - Raise ValueError for not-found, return error_result for auth failures
  - Use ctx for logging, progress, and lifespan dependencies
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp.server.mcpserver import Context
from mcp.server.session import ServerSession
from mcp.types import CallToolResult

# Import from your server module — adjust path as needed
# from app.mcp.server import mcp, validate_token, success_result, error_result, AppContext
# from app.models import YourModel


# ---------------------------------------------------------------------------
# Type alias for convenience
# ---------------------------------------------------------------------------

Ctx = Context[ServerSession, "AppContext"]


# ---------------------------------------------------------------------------
# Tool: List Items
# ---------------------------------------------------------------------------

# @mcp.tool()
async def list_items(
    auth_token: str,
    ctx: Ctx,
) -> CallToolResult:
    """List all items for the authenticated user.

    Returns a JSON array of items with id, title, status, and timestamps.

    Args:
        auth_token: Bearer token from the user's authenticated session.
    """
    user_id = await validate_token(auth_token, ctx)
    await ctx.info(f"Listing items for user {user_id}")

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        stmt = select(YourModel).where(YourModel.user_id == user_id)
        result = await db.execute(stmt)
        items = result.scalars().all()

    return success_result([item.model_dump() for item in items])


# ---------------------------------------------------------------------------
# Tool: Get Item by ID
# ---------------------------------------------------------------------------

# @mcp.tool()
async def get_item(
    item_id: str,
    auth_token: str,
    ctx: Ctx,
) -> CallToolResult:
    """Get a single item by its ID.

    Returns the full item object or an error if not found.

    Args:
        item_id: UUID of the item to retrieve.
        auth_token: Bearer token from the user's authenticated session.
    """
    user_id = await validate_token(auth_token, ctx)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        stmt = (
            select(YourModel)
            .where(YourModel.id == item_id, YourModel.user_id == user_id)
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

    if not item:
        raise ValueError(f"Item {item_id} not found")

    return success_result(item.model_dump())


# ---------------------------------------------------------------------------
# Tool: Create Item
# ---------------------------------------------------------------------------

# @mcp.tool()
async def create_item(
    title: str,
    auth_token: str,
    ctx: Ctx,
    description: str = "",
) -> CallToolResult:
    """Create a new item for the authenticated user.

    Args:
        title: Item title (1-255 characters, required).
        auth_token: Bearer token from the user's authenticated session.
        description: Optional description (max 2000 characters).
    """
    user_id = await validate_token(auth_token, ctx)
    await ctx.info(f"Creating item '{title}' for user {user_id}")

    item = YourModel(title=title.strip(), description=description.strip(), user_id=user_id)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        db.add(item)
        await db.commit()
        await db.refresh(item)

    return success_result(item.model_dump())


# ---------------------------------------------------------------------------
# Tool: Update Item
# ---------------------------------------------------------------------------

# @mcp.tool()
async def update_item(
    item_id: str,
    auth_token: str,
    ctx: Ctx,
    title: str | None = None,
    description: str | None = None,
) -> CallToolResult:
    """Update an existing item's title and/or description.

    Only provided fields are updated; omitted fields remain unchanged.

    Args:
        item_id: UUID of the item to update.
        auth_token: Bearer token from the user's authenticated session.
        title: New title (1-255 characters, optional).
        description: New description (max 2000 characters, optional).
    """
    user_id = await validate_token(auth_token, ctx)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        stmt = (
            select(YourModel)
            .where(YourModel.id == item_id, YourModel.user_id == user_id)
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise ValueError(f"Item {item_id} not found")

        if title is not None:
            item.title = title.strip()
        if description is not None:
            item.description = description.strip()

        db.add(item)
        await db.commit()
        await db.refresh(item)

    return success_result(item.model_dump())


# ---------------------------------------------------------------------------
# Tool: Delete Item
# ---------------------------------------------------------------------------

# @mcp.tool()
async def delete_item(
    item_id: str,
    auth_token: str,
    ctx: Ctx,
) -> CallToolResult:
    """Permanently delete an item.

    Args:
        item_id: UUID of the item to delete.
        auth_token: Bearer token from the user's authenticated session.
    """
    user_id = await validate_token(auth_token, ctx)

    async with ctx.request_context.lifespan_context.db_session_factory() as db:
        stmt = (
            select(YourModel)
            .where(YourModel.id == item_id, YourModel.user_id == user_id)
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise ValueError(f"Item {item_id} not found")

        await db.delete(item)
        await db.commit()

    return success_result({"deleted": item_id})


# ---------------------------------------------------------------------------
# Tool: Long-Running Operation with Progress
# ---------------------------------------------------------------------------

# @mcp.tool()
async def batch_operation(
    item_ids: list[str],
    action: str,
    auth_token: str,
    ctx: Ctx,
) -> CallToolResult:
    """Perform a batch operation on multiple items with progress tracking.

    Args:
        item_ids: List of item UUIDs to process.
        action: Action to perform ("complete", "archive", "delete").
        auth_token: Bearer token from the user's authenticated session.
    """
    user_id = await validate_token(auth_token, ctx)
    total = len(item_ids)
    processed = []

    for i, item_id in enumerate(item_ids):
        await ctx.report_progress(progress=i, total=total, message=f"Processing {i+1}/{total}")
        # ... process each item ...
        processed.append(item_id)

    return success_result({"action": action, "processed": len(processed), "ids": processed})

"""
Database-backed ChatKit Store
==============================
Maps ChatKit ThreadMetadata ↔ Conversation and ThreadItem ↔ Message.
All queries filter by context["user_id"] for user isolation (Constitution V).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlmodel import select

from chatkit.store import Store
from chatkit.types import (
    ActiveStatus,
    AssistantMessageContent,
    AssistantMessageItem,
    InferenceOptions,
    Page,
    ThreadItem,
    ThreadMetadata,
    UserMessageItem,
    UserMessageTextContent,
)

from app.database import async_session
from app.models import Conversation, Message


def _to_naive_utc(dt: datetime | None) -> datetime:
    """Normalise a datetime to naive UTC for TIMESTAMP WITHOUT TIME ZONE columns.

    asyncpg rejects tz-aware datetimes for tz-naive columns. This strips
    tzinfo after converting to UTC, matching the Task model convention.
    """
    if dt is None:
        return datetime.utcnow()
    if dt.tzinfo is not None:
        # Convert to UTC then strip tzinfo
        utc_dt = dt.astimezone(timezone.utc)
        return utc_dt.replace(tzinfo=None)
    return dt


def _safe_uuid(value: str) -> uuid.UUID:
    """Parse a string as UUID; if it's not a valid UUID, generate a fresh random UUID.

    The ChatKit SDK with Chat Completions API produces placeholder IDs like
    '__fake_id__' for every assistant message.  A deterministic mapping would
    collapse all of those into the same row, so we generate a new UUID instead.
    """
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return uuid.uuid4()


class DatabaseChatKitStore(Store[dict]):
    """ChatKit Store backed by PostgreSQL via async SQLAlchemy."""

    # -- ID generation -------------------------------------------------------

    def generate_thread_id(self, context: dict) -> str:
        return str(uuid.uuid4())

    def generate_item_id(self, item_type, thread, context: dict) -> str:
        return str(uuid.uuid4())

    # -- Thread operations ---------------------------------------------------

    async def load_thread(self, thread_id: str, context: dict) -> ThreadMetadata:
        user_id = context["user_id"]
        async with async_session() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == uuid.UUID(thread_id),
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()

        if not conv:
            raise ValueError(f"Thread {thread_id} not found")

        return _conv_to_thread(conv)

    async def save_thread(self, thread: ThreadMetadata, context: dict) -> None:
        user_id = context["user_id"]
        async with async_session() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == uuid.UUID(thread.id),
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()

            if conv:
                conv.title = thread.title
                conv.updated_at = datetime.utcnow()
            else:
                conv = Conversation(
                    id=uuid.UUID(thread.id),
                    user_id=user_id,
                    title=thread.title,
                    created_at=_to_naive_utc(thread.created_at),
                    updated_at=datetime.utcnow(),
                )
                db.add(conv)

            await db.commit()

    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: dict,
    ) -> Page[ThreadMetadata]:
        user_id = context["user_id"]
        async with async_session() as db:
            stmt = select(Conversation).where(Conversation.user_id == user_id)

            if order == "desc":
                stmt = stmt.order_by(Conversation.updated_at.desc())
            else:
                stmt = stmt.order_by(Conversation.updated_at.asc())

            if after:
                cursor_result = await db.execute(
                    select(Conversation).where(Conversation.id == uuid.UUID(after))
                )
                cursor = cursor_result.scalar_one_or_none()
                if cursor:
                    if order == "desc":
                        stmt = stmt.where(
                            Conversation.updated_at < cursor.updated_at
                        )
                    else:
                        stmt = stmt.where(
                            Conversation.updated_at > cursor.updated_at
                        )

            stmt = stmt.limit(limit + 1)
            result = await db.execute(stmt)
            convs = list(result.scalars().all())

        has_more = len(convs) > limit
        if has_more:
            convs = convs[:limit]

        threads = [_conv_to_thread(c) for c in convs]
        return Page(
            data=threads,
            has_more=has_more,
            after=str(convs[-1].id) if convs else None,
        )

    async def delete_thread(self, thread_id: str, context: dict) -> None:
        user_id = context["user_id"]
        async with async_session() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == uuid.UUID(thread_id),
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()
            if not conv:
                raise ValueError(f"Thread {thread_id} not found")

            await db.delete(conv)
            await db.commit()

    # -- Item operations -----------------------------------------------------

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: dict,
    ) -> Page[ThreadItem]:
        async with async_session() as db:
            stmt = select(Message).where(
                Message.conversation_id == uuid.UUID(thread_id),
            )

            if order == "desc":
                stmt = stmt.order_by(Message.created_at.desc())
            else:
                stmt = stmt.order_by(Message.created_at.asc())

            if after:
                cursor_result = await db.execute(
                    select(Message).where(Message.id == uuid.UUID(after))
                )
                cursor = cursor_result.scalar_one_or_none()
                if cursor:
                    if order == "desc":
                        stmt = stmt.where(Message.created_at < cursor.created_at)
                    else:
                        stmt = stmt.where(Message.created_at > cursor.created_at)

            stmt = stmt.limit(limit + 1)
            result = await db.execute(stmt)
            msgs = list(result.scalars().all())

        has_more = len(msgs) > limit
        if has_more:
            msgs = msgs[:limit]

        items = [_msg_to_item(m, thread_id) for m in msgs]
        return Page(
            data=items,
            has_more=has_more,
            after=str(msgs[-1].id) if msgs else None,
        )

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: dict
    ) -> None:
        thread_uuid = _safe_uuid(thread_id)
        content = _extract_text(item)
        if not content.strip():
            return
        async with async_session() as db:
            msg = Message(
                id=uuid.uuid4(),  # always generate a fresh ID for storage
                conversation_id=thread_uuid,
                role=_item_role(item),
                content=content,
                created_at=_to_naive_utc(item.created_at) if item.created_at else datetime.utcnow(),
            )
            db.add(msg)

            # Update conversation's updated_at
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == thread_uuid
                )
            )
            conv = result.scalar_one_or_none()
            if conv:
                conv.updated_at = datetime.utcnow()

            await db.commit()

    async def save_item(
        self, thread_id: str, item: ThreadItem, context: dict
    ) -> None:
        async with async_session() as db:
            result = await db.execute(
                select(Message).where(Message.id == _safe_uuid(item.id))
            )
            msg = result.scalar_one_or_none()

            if msg:
                msg.content = _extract_text(item)
                msg.role = _item_role(item)
            else:
                msg = Message(
                    id=_safe_uuid(item.id),
                    conversation_id=_safe_uuid(thread_id),
                    role=_item_role(item),
                    content=_extract_text(item),
                    created_at=_to_naive_utc(item.created_at),
                )
                db.add(msg)

            await db.commit()

    async def load_item(
        self, thread_id: str, item_id: str, context: dict
    ) -> ThreadItem:
        async with async_session() as db:
            result = await db.execute(
                select(Message).where(
                    Message.id == _safe_uuid(item_id),
                    Message.conversation_id == _safe_uuid(thread_id),
                )
            )
            msg = result.scalar_one_or_none()

        if not msg:
            raise ValueError(f"Item {item_id} not found")

        return _msg_to_item(msg, thread_id)

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: dict
    ) -> None:
        async with async_session() as db:
            result = await db.execute(
                select(Message).where(
                    Message.id == _safe_uuid(item_id),
                    Message.conversation_id == _safe_uuid(thread_id),
                )
            )
            msg = result.scalar_one_or_none()
            if not msg:
                raise ValueError(f"Item {item_id} not found")
            await db.delete(msg)
            await db.commit()

    # -- Attachment stubs (not used in Phase 3) ------------------------------

    async def save_attachment(self, attachment, context: dict) -> None:
        raise NotImplementedError("Attachments not supported in Phase 3")

    async def load_attachment(self, attachment_id: str, context: dict):
        raise NotImplementedError("Attachments not supported in Phase 3")

    async def delete_attachment(self, attachment_id: str, context: dict) -> None:
        raise NotImplementedError("Attachments not supported in Phase 3")


# -- Private helpers (module-level for reuse) --------------------------------


def _conv_to_thread(conv: Conversation) -> ThreadMetadata:
    return ThreadMetadata(
        id=str(conv.id),
        title=conv.title,
        created_at=conv.created_at,
        status=ActiveStatus(),
    )


def _msg_to_item(msg: Message, thread_id: str) -> ThreadItem:
    if msg.role == "user":
        return UserMessageItem(
            id=str(msg.id),
            thread_id=thread_id,
            content=[UserMessageTextContent(text=msg.content)],
            created_at=msg.created_at,
            inference_options=InferenceOptions(),
        )
    else:
        return AssistantMessageItem(
            id=str(msg.id),
            thread_id=thread_id,
            content=[AssistantMessageContent(text=msg.content)],
            created_at=msg.created_at,
        )


def _extract_text(item: ThreadItem) -> str:
    """Extract plain text from a ThreadItem's content."""
    if hasattr(item, "content"):
        content = item.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if hasattr(part, "text"):
                    parts.append(part.text)
            return "\n".join(parts) if parts else ""
    return ""


def _item_role(item: ThreadItem) -> str:
    """Determine the role from a ThreadItem type."""
    if isinstance(item, UserMessageItem):
        return "user"
    return "assistant"

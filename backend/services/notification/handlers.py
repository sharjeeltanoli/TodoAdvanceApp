"""Notification event handlers — processes reminder events and manages notifications."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models import Notification, ProcessedEvent

logger = logging.getLogger(__name__)

router = APIRouter()


async def check_and_mark_processed(event_id: str, consumer_group: str, db: AsyncSession) -> bool:
    """Check if event was already processed. Returns True if already processed."""
    result = await db.execute(
        select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
    )
    if result.scalar_one_or_none():
        return True
    record = ProcessedEvent(
        event_id=event_id,
        consumer_group=consumer_group,
        processed_at=datetime.utcnow(),
    )
    db.add(record)
    await db.commit()
    return False


@router.post("/events/reminder")
async def handle_reminder_event(request: Request):
    """Handle reminder events from Dapr pub/sub.

    Creates Notification records in PostgreSQL, with idempotency check.
    """
    from main import get_db_session

    envelope = await request.json()
    data = envelope.get("data", {})
    event_id = envelope.get("id", "")

    async with get_db_session() as db:
        # Check idempotency
        if event_id and await check_and_mark_processed(event_id, "notification-svc-group", db):
            logger.info("Event already processed", extra={"event_id": event_id})
            return {"status": "SUCCESS"}

        reminder_type = data.get("reminder_type", "upcoming")
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        title = data.get("title", "Task reminder")
        due_date = data.get("due_date", "")

        if not user_id:
            return {"status": "SUCCESS"}

        # Map reminder type to notification type
        notif_type = f"reminder_{reminder_type}"  # reminder_upcoming or reminder_overdue

        # Create notification body
        if reminder_type == "overdue":
            body = f'"{title}" is overdue (due: {due_date})'
        else:
            body = f'"{title}" is due soon ({due_date})'

        notification = Notification(
            user_id=user_id,
            type=notif_type,
            title=f"Task {reminder_type.title()}" if reminder_type == "overdue" else "Task Reminder",
            body=body,
            task_id=uuid.UUID(task_id) if task_id else None,
            read=False,
            created_at=datetime.utcnow(),
        )
        db.add(notification)
        await db.commit()

        logger.info(
            "Created notification",
            extra={"user_id": user_id, "type": notif_type, "task_id": task_id},
        )

    return {"status": "SUCCESS"}

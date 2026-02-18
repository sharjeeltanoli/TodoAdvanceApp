"""Event subscriber handlers for Dapr pub/sub."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import async_session
from app.events.publisher import (
    check_and_mark_processed,
    dapr_publish,
    get_state,
    publish_task_event,
    save_state,
)
from app.events.schemas import ReminderEventData
from app.models import Task

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Events"])


@router.post("/events/task")
async def handle_task_event(request: Request):
    """Handle task-events from Dapr pub/sub.

    Processes task.completed events for recurring task generation (US3).
    Uses idempotency check to prevent duplicate processing.
    """
    envelope = await request.json()
    data = envelope.get("data", {})
    event_id = envelope.get("id", "")
    event_type = data.get("event_type", "")

    async with async_session() as db:
        # Check idempotency
        if event_id and await check_and_mark_processed(event_id, "recurring-handler-group", db):
            logger.info("Event already processed", extra={"event_id": event_id})
            return {"status": "SUCCESS"}

        # Only process completed events for recurring task generation
        if event_type == "completed":
            await _handle_task_completed(data, db)

    return {"status": "SUCCESS"}


async def _handle_task_completed(data: dict, db: AsyncSession) -> None:
    """Handle task.completed event — generate next recurring task if applicable."""
    task_id = data.get("task_id")
    user_id = data.get("user_id")

    if not task_id or not user_id:
        return

    # Fetch the completed task
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task or not task.recurrence_pattern:
        return

    pattern = task.recurrence_pattern
    freq = pattern.get("frequency", "daily")
    interval = pattern.get("interval", 1)

    # Compute next due date
    base_date = task.due_date or datetime.utcnow()
    if freq == "daily":
        next_due = base_date + timedelta(days=interval)
    elif freq == "weekly":
        next_due = base_date + timedelta(weeks=interval)
    elif freq == "monthly":
        month = base_date.month + interval
        year = base_date.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day = min(base_date.day, 28)
        next_due = base_date.replace(year=year, month=month, day=day)
    else:
        next_due = base_date + timedelta(days=1)

    # Create new task with inherited properties
    new_task = Task(
        user_id=user_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        tags=list(task.tags) if task.tags else [],
        due_date=next_due,
        recurrence_pattern={
            "frequency": freq,
            "interval": interval,
            "next_due": next_due.isoformat(),
        },
        reminder_minutes=task.reminder_minutes,
        parent_task_id=task.id,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    logger.info(
        "Created recurring task",
        extra={
            "original_task_id": str(task.id),
            "new_task_id": str(new_task.id),
            "next_due": next_due.isoformat(),
        },
    )

    # Publish task.created event for the new task
    await publish_task_event("created", new_task, user_id, db)


# --- Cron Handler (T036) ---


@router.post("/cron-overdue-check")
async def cron_overdue_check(request: Request):
    """Handle Dapr cron binding — check for upcoming and overdue tasks.

    Called every 5 minutes by Dapr cron-overdue-check binding.
    Publishes reminder.upcoming and reminder.overdue events to reminders topic.
    Uses Dapr state store for deduplication (5-minute TTL per FR-008).
    """
    async with async_session() as db:
        now = datetime.utcnow()
        one_hour_from_now = now + timedelta(hours=1)

        # Query tasks with upcoming due dates (within 1 hour)
        upcoming_stmt = select(Task).where(
            Task.due_date.isnot(None),
            Task.due_date <= one_hour_from_now,
            Task.due_date > now,
            Task.completed == False,
        )
        result = await db.execute(upcoming_stmt)
        upcoming_tasks = result.scalars().all()

        # Query overdue tasks
        overdue_stmt = select(Task).where(
            Task.due_date.isnot(None),
            Task.due_date < now,
            Task.completed == False,
        )
        result = await db.execute(overdue_stmt)
        overdue_tasks = result.scalars().all()

        published = 0

        # Process upcoming tasks
        for task in upcoming_tasks:
            window = task.due_date.strftime("%Y%m%d%H")
            dedup_key = f"reminder:{task.id}:{window}"

            existing = await get_state(dedup_key)
            if existing:
                continue

            reminder = ReminderEventData(
                reminder_type="upcoming",
                task_id=str(task.id),
                user_id=task.user_id,
                title=task.title,
                due_date=task.due_date.isoformat(),
                link=f"/dashboard?task={task.id}",
            )
            await dapr_publish("reminders", "reminder.upcoming", reminder.to_dict())
            await save_state(dedup_key, {"sent": True}, ttl=300)
            published += 1

        # Process overdue tasks
        for task in overdue_tasks:
            date_key = now.strftime("%Y%m%d")
            dedup_key = f"overdue:{task.id}:{date_key}"

            existing = await get_state(dedup_key)
            if existing:
                continue

            reminder = ReminderEventData(
                reminder_type="overdue",
                task_id=str(task.id),
                user_id=task.user_id,
                title=task.title,
                due_date=task.due_date.isoformat(),
                link=f"/dashboard?task={task.id}",
            )
            await dapr_publish("reminders", "reminder.overdue", reminder.to_dict())
            await save_state(dedup_key, {"sent": True}, ttl=86400)
            published += 1

        logger.info(
            "Cron overdue check completed",
            extra={
                "upcoming_checked": len(upcoming_tasks),
                "overdue_checked": len(overdue_tasks),
                "reminders_published": published,
            },
        )

    return {"status": "SUCCESS"}

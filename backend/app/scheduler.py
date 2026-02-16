"""Recurring task scheduler — generates new task instances when next_due arrives."""

import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Task

logger = logging.getLogger(__name__)


async def process_recurring_tasks(db: AsyncSession) -> int:
    """Check for recurring tasks needing new instances. Returns count of created tasks."""
    now = datetime.utcnow()
    stmt = select(Task).where(
        Task.recurrence_pattern.isnot(None),
        Task.completed == False,
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    created = 0
    for task in tasks:
        pattern = task.recurrence_pattern
        if not pattern or "next_due" not in pattern:
            continue

        next_due = datetime.fromisoformat(pattern["next_due"].replace("Z", "+00:00"))
        if next_due > now:
            continue

        # Create child task
        child = Task(
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            tags=list(task.tags) if task.tags else [],
            due_date=next_due,
            parent_task_id=task.id,
        )
        db.add(child)

        # Advance next_due
        freq = pattern.get("frequency", "daily")
        interval = pattern.get("interval", 1)
        if freq == "daily":
            new_next = next_due + timedelta(days=interval)
        elif freq == "weekly":
            new_next = next_due + timedelta(weeks=interval)
        elif freq == "monthly":
            # Simple month advancement
            month = next_due.month + interval
            year = next_due.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = min(next_due.day, 28)  # Safe day
            new_next = next_due.replace(year=year, month=month, day=day)
        else:
            new_next = next_due + timedelta(days=1)

        task.recurrence_pattern = {
            **pattern,
            "next_due": new_next.isoformat(),
        }
        created += 1

    if created:
        await db.commit()
        logger.info(f"Created {created} recurring task instance(s)")

    return created

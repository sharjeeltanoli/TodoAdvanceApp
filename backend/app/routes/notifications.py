"""Notification routes — direct DB implementation (no Dapr dependency)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user
from app.models import Notification, Task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


async def _sync_task_notifications(user_id: str, db: AsyncSession) -> None:
    """Generate notification records for due-soon and overdue tasks (idempotent).

    Uses naive UTC datetimes throughout — the DB columns are TIMESTAMP WITHOUT
    TIME ZONE and asyncpg rejects timezone-aware datetimes against them.
    """
    now = datetime.utcnow()  # naive UTC — matches DB column type
    cutoff_24h = now + timedelta(hours=24)

    # Fetch incomplete tasks that are due or overdue
    result = await db.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.completed == False,
            Task.due_date != None,
            Task.due_date <= cutoff_24h,
        )
    )
    tasks = result.scalars().all()

    if not tasks:
        return

    # Fetch existing recent notifications for these tasks to avoid duplicates
    task_ids = [t.id for t in tasks]
    recent_cutoff = now - timedelta(hours=6)
    existing_result = await db.execute(
        select(Notification.task_id, Notification.type).where(
            Notification.user_id == user_id,
            Notification.task_id.in_(task_ids),
            Notification.created_at >= recent_cutoff,
        )
    )
    existing_pairs = set(existing_result.all())

    new_notifications = []
    for task in tasks:
        due = task.due_date
        # Strip tzinfo if present — keep comparison naive
        if due.tzinfo is not None:
            due = due.replace(tzinfo=None)

        if due < now:
            ntype = "reminder_overdue"
            title = f"Overdue: {task.title}"
            body = f"This task was due {_humanize_delta(now - due)} ago."
        else:
            ntype = "reminder_upcoming"
            title = f"Due soon: {task.title}"
            body = f"Due in {_humanize_delta(due - now)}."

        if (task.id, ntype) not in existing_pairs:
            new_notifications.append(
                Notification(
                    user_id=user_id,
                    type=ntype,
                    title=title,
                    body=body,
                    task_id=task.id,
                )
            )

    if new_notifications:
        db.add_all(new_notifications)
        await db.commit()


def _humanize_delta(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds < 3600:
        minutes = max(1, total_seconds // 60)
        return f"{minutes}m"
    if total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}h"
    days = total_seconds // 86400
    return f"{days}d"


@router.get("/unread-count")
async def unread_count(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Count unread notifications for the current user."""
    await _sync_task_notifications(user_id, db)
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.read == False,
        )
    )
    return {"count": result.scalar() or 0}


@router.get("")
async def list_notifications(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    unread_only: bool = Query(False),
    limit: int = Query(20, le=50),
):
    """List notifications for the current user."""
    await _sync_task_notifications(user_id, db)
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.read == False)
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    return {
        "notifications": [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "task_id": str(n.task_id) if n.task_id else None,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }


@router.patch("/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == uuid.UUID(notif_id),
            Notification.user_id == user_id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    db.add(notif)
    await db.commit()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Mark all notifications as read."""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read == False)
        .values(read=True)
    )
    await db.commit()
    return {"ok": True}

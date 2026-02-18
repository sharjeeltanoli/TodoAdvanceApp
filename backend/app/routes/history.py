"""Task event history / audit trail endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import TaskEvent
from app.routes.todos import get_current_user

router = APIRouter(prefix="/api", tags=["History"])


@router.get("/todos/{task_id}/history")
async def get_task_history(
    task_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Return chronological event history for a task.

    Only returns events belonging to the authenticated user.
    """
    stmt = (
        select(TaskEvent)
        .where(TaskEvent.task_id == task_id, TaskEvent.user_id == user_id)
        .order_by(TaskEvent.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    if not events and offset == 0:
        # Verify the task exists and belongs to user before returning empty
        from app.models import Task

        task_check = await db.execute(
            select(Task.id).where(Task.id == task_id, Task.user_id == user_id)
        )
        if not task_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Task not found")

    return {
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "changed_fields": e.changed_fields,
                "data": e.data,
                "event_source": e.event_source,
            }
            for e in events
        ],
        "total": len(events),
        "limit": limit,
        "offset": offset,
    }

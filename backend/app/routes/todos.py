import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.dependencies import get_current_user
from app.events.publisher import publish_task_event
from app.models import Task, TaskCreate, TaskUpdate, TaskResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tasks"])

PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}


@router.post("/todos", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    data: TaskCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    dump = data.model_dump()
    # Convert RecurrencePattern to dict for JSON storage
    if dump.get("recurrence_pattern") is not None:
        dump["recurrence_pattern"] = data.recurrence_pattern.model_dump(mode="json")
    task = Task(**dump, user_id=user_id)
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Fire-and-forget event publishing
    asyncio.create_task(publish_task_event("created", task, user_id, db))

    return task


@router.get("/todos", response_model=list[TaskResponse])
async def list_todos(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    search: Optional[str] = Query(None, description="Search title and description"),
    status_filter: Optional[str] = Query(None, alias="status", description="pending or completed"),
    priority: Optional[str] = Query(None, description="high, medium, or low"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    sort_by: Optional[str] = Query(None, description="created_at, due_date, or priority"),
    sort_dir: Optional[str] = Query("desc", description="asc or desc"),
):
    stmt = select(Task).where(Task.user_id == user_id)

    # Search filter
    if search:
        escaped = search.replace("%", r"\%").replace("_", r"\_")
        pattern = f"%{escaped}%"
        stmt = stmt.where(
            or_(
                Task.title.ilike(pattern),
                Task.description.ilike(pattern),
            )
        )

    # Status filter
    if status_filter == "pending":
        stmt = stmt.where(Task.completed == False)
    elif status_filter == "completed":
        stmt = stmt.where(Task.completed == True)

    # Priority filter
    if priority and priority in ("high", "medium", "low"):
        stmt = stmt.where(Task.priority == priority)

    # Tag filter (JSONB containment)
    if tag:
        stmt = stmt.where(Task.tags.contains([tag]))

    # Sorting
    if sort_by == "due_date":
        if sort_dir == "asc":
            stmt = stmt.order_by(Task.due_date.asc().nulls_last())
        else:
            stmt = stmt.order_by(Task.due_date.desc().nulls_last())
    elif sort_by == "priority":
        # Use CASE expression for priority ordering
        priority_case = func.case(
            (Task.priority == "high", 1),
            (Task.priority == "medium", 2),
            (Task.priority == "low", 3),
            else_=2,
        )
        if sort_dir == "asc":
            stmt = stmt.order_by(priority_case.asc())
        else:
            stmt = stmt.order_by(priority_case.asc())  # "highest" = high first
    else:
        # Default: created_at
        if sort_dir == "asc":
            stmt = stmt.order_by(Task.created_at.asc())
        else:
            stmt = stmt.order_by(Task.created_at.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/todos/tags", response_model=list[str])
async def list_tags(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Return distinct tags for the current user, sorted alphabetically."""
    from sqlalchemy import text
    result = await db.execute(
        text(
            "SELECT DISTINCT jsonb_array_elements_text(tags) AS tag "
            "FROM task WHERE user_id = :uid ORDER BY tag"
        ),
        {"uid": user_id},
    )
    return [row[0] for row in result.fetchall()]


@router.get("/todos/reminders", response_model=list[TaskResponse])
async def list_reminders(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Return tasks with active reminders whose trigger time has passed."""
    now = datetime.utcnow()
    stmt = (
        select(Task)
        .where(
            Task.user_id == user_id,
            Task.completed == False,
            Task.due_date.isnot(None),
            Task.reminder_minutes.isnot(None),
        )
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    due_tasks = []
    for task in tasks:
        from datetime import timedelta
        trigger_time = task.due_date - timedelta(minutes=task.reminder_minutes)
        if trigger_time <= now:
            # Skip if already notified and not snoozed
            if task.reminder_notified_at is not None:
                if task.snoozed_until is None or task.snoozed_until > now:
                    continue
            due_tasks.append(task)
    return due_tasks


@router.get("/todos/{task_id}", response_model=TaskResponse)
async def get_todo(
    task_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/todos/{task_id}", response_model=TaskResponse)
async def update_todo(
    task_id: uuid.UUID,
    data: TaskUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = data.model_dump(exclude_unset=True)
    # Track changes for event payload
    changed_fields = {}
    for key, value in update_data.items():
        old_val = getattr(task, key, None)
        if old_val != value:
            changed_fields[key] = {"old": old_val, "new": value}
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    # Fire-and-forget event publishing
    if changed_fields:
        asyncio.create_task(publish_task_event("updated", task, user_id, db, changed_fields))

    return task


@router.delete("/todos/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    task_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Publish event before deletion (need task data for event)
    asyncio.create_task(publish_task_event("deleted", task, user_id, db))

    await db.delete(task)
    await db.commit()


@router.patch("/todos/{task_id}/complete", response_model=TaskResponse)
async def toggle_complete(
    task_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    old_completed = task.completed
    task.completed = not task.completed
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    # Fire-and-forget event publishing
    event_type = "completed" if task.completed else "updated"
    changed = {"completed": {"old": old_completed, "new": task.completed}}
    asyncio.create_task(publish_task_event(event_type, task, user_id, db, changed))

    return task


@router.post("/todos/{task_id}/snooze", response_model=TaskResponse)
async def snooze_reminder(
    task_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Snooze a task reminder for 15 minutes."""
    from datetime import timedelta
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.reminder_minutes is None:
        raise HTTPException(status_code=400, detail="Task has no reminder set")
    task.snoozed_until = datetime.utcnow() + timedelta(minutes=15)
    task.reminder_notified_at = None
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    return task

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.dependencies import get_current_user
from app.models import Task, TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(tags=["Tasks"])


@router.post("/todos", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    data: TaskCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    task = Task(**data.model_dump(), user_id=user_id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/todos", response_model=list[TaskResponse])
async def list_todos(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
    )
    return result.scalars().all()


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
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
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
    task.completed = not task.completed
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    return task

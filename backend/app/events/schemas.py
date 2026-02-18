"""Event schema dataclasses for Dapr pub/sub messages."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class TaskEventData:
    """Full task event payload published to task-events topic."""
    event_type: str  # created, updated, deleted, completed
    task_id: str
    user_id: str
    task: dict[str, Any] | None = None  # null for delete events
    changed_fields: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReminderEventData:
    """Reminder event payload published to reminders topic."""
    reminder_type: str  # upcoming, overdue
    task_id: str
    user_id: str
    title: str
    due_date: str  # ISO 8601
    link: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TaskUpdateData:
    """Lightweight task update payload published to task-updates topic for SSE sync."""
    change_type: str  # created, updated, deleted, completed
    task_id: str
    user_id: str
    changed_fields: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def task_to_snapshot(task) -> dict[str, Any]:
    """Convert a Task SQLModel instance to a serializable snapshot dict."""
    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "priority": task.priority,
        "tags": list(task.tags) if task.tags else [],
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "recurrence_pattern": task.recurrence_pattern,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }

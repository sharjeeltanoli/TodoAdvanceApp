import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, field_validator
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class RecurrencePattern(BaseModel):
    frequency: str  # daily, weekly, monthly
    interval: int = 1
    next_due: datetime

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        if v not in ("daily", "weekly", "monthly"):
            raise ValueError("frequency must be daily, weekly, or monthly")
        return v


class TaskBase(SQLModel):
    title: str = Field(max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace-only")
        return v.strip()


class TaskCreate(TaskBase):
    priority: str = "medium"
    tags: list[str] = []
    due_date: datetime | None = None
    recurrence_pattern: RecurrencePattern | None = None
    reminder_minutes: int | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in ("high", "medium", "low"):
            raise ValueError("priority must be high, medium, or low")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return [t.lower().strip() for t in v]

    @field_validator("reminder_minutes")
    @classmethod
    def validate_reminder_minutes(cls, v: int | None) -> int | None:
        if v is not None and v not in (15, 60, 1440):
            raise ValueError("reminder_minutes must be 15, 60, or 1440")
        return v


class TaskUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=2000)
    priority: str | None = None
    tags: list[str] | None = None
    due_date: datetime | None = None
    recurrence_pattern: dict[str, Any] | None = None
    reminder_minutes: int | None = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace-only")
        return v.strip() if v else v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str | None) -> str | None:
        if v is not None and v not in ("high", "medium", "low"):
            raise ValueError("priority must be high, medium, or low")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            return [t.lower().strip() for t in v]
        return v

    @field_validator("reminder_minutes")
    @classmethod
    def validate_reminder_minutes(cls, v: int | None) -> int | None:
        if v is not None and v not in (15, 60, 1440):
            raise ValueError("reminder_minutes must be 15, 60, or 1440")
        return v


class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # New fields
    priority: str = Field(default="medium")
    tags: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, server_default="[]"))
    due_date: datetime | None = Field(default=None)
    recurrence_pattern: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    reminder_minutes: int | None = Field(default=None)
    snoozed_until: datetime | None = Field(default=None)
    reminder_notified_at: datetime | None = Field(default=None)
    parent_task_id: uuid.UUID | None = Field(default=None, foreign_key="task.id")


class TaskResponse(TaskBase):
    id: uuid.UUID
    completed: bool
    created_at: datetime
    updated_at: datetime
    priority: str
    tags: list[str]
    due_date: datetime | None
    recurrence_pattern: dict[str, Any] | None
    reminder_minutes: int | None
    snoozed_until: datetime | None
    reminder_notified_at: datetime | None
    parent_task_id: uuid.UUID | None


# --- Phase 3: Conversation & Message models ---


class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", index=True)
    role: str = Field(max_length=20)  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

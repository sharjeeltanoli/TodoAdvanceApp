import uuid
from datetime import datetime

from pydantic import field_validator
from sqlmodel import SQLModel, Field


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
    pass


class TaskUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace-only")
        return v.strip() if v else v


class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskResponse(TaskBase):
    id: uuid.UUID
    completed: bool
    created_at: datetime
    updated_at: datetime


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

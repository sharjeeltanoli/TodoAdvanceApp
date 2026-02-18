"""Notification service models — mirrors the main backend models for DB access."""

import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class Notification(SQLModel, table=True):
    """Stores in-app notifications for users."""
    __tablename__ = "notification"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(max_length=255, nullable=False, index=True)
    type: str = Field(max_length=30, nullable=False)
    title: str = Field(max_length=255, nullable=False)
    body: str | None = Field(default=None)
    task_id: uuid.UUID | None = Field(default=None)
    read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessedEvent(SQLModel, table=True):
    """Tracks processed event IDs for consumer idempotency."""
    __tablename__ = "processed_event"

    event_id: str = Field(max_length=255, primary_key=True)
    consumer_group: str = Field(max_length=100, nullable=False)
    processed_at: datetime = Field(default_factory=datetime.utcnow)

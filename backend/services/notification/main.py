"""Notification Service — subscribes to reminders topic, manages notification CRUD."""

from __future__ import annotations

import logging
import ssl
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select, func

from models import Notification, ProcessedEvent  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    model_config = {"env_file": ".env"}

    @property
    def async_database_url(self) -> str:
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params.pop("sslmode", None)
        params.pop("channel_binding", None)
        return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))


settings = Settings()

ssl_context = ssl.create_default_context()
engine = create_async_engine(
    settings.async_database_url,
    connect_args={"ssl": ssl_context},
    pool_pre_ping=True,
    pool_recycle=300,
)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_db_session():
    async with async_session_factory() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Notification service starting")
    yield
    await engine.dispose()


app = FastAPI(title="Notification Service", version="1.0.0", lifespan=lifespan)

# Import and register handlers
from handlers import router as handler_router  # noqa: E402
app.include_router(handler_router)


# --- Dapr Subscription ---


@app.get("/dapr/subscribe")
async def dapr_subscribe():
    return [
        {
            "pubsubname": "pubsub",
            "topic": "reminders",
            "route": "/events/reminder",
        },
    ]


# --- Notification REST Endpoints (T041) ---


@app.get("/notifications")
async def list_notifications(
    user_id: str,
    unread_only: bool = Query(False),
    limit: int = Query(20, le=50),
    cursor: Optional[str] = Query(None),
):
    """List notifications for a user with cursor pagination."""
    async with get_db_session() as db:
        stmt = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            stmt = stmt.where(Notification.read == False)

        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor)
                stmt = stmt.where(Notification.created_at < cursor_dt)
            except ValueError:
                pass

        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit + 1)
        result = await db.execute(stmt)
        notifications = result.scalars().all()

        has_more = len(notifications) > limit
        if has_more:
            notifications = notifications[:limit]

        next_cursor = None
        if has_more and notifications:
            next_cursor = notifications[-1].created_at.isoformat()

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
            ],
            "next_cursor": next_cursor,
        }


@app.patch("/notifications/{notif_id}/read")
async def mark_as_read(notif_id: uuid.UUID, user_id: str):
    """Mark a notification as read."""
    async with get_db_session() as db:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notif_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.read = True
        await db.commit()
        return {"status": "ok"}


@app.post("/notifications/read-all")
async def mark_all_read(user_id: str):
    """Mark all notifications as read for a user."""
    async with get_db_session() as db:
        from sqlalchemy import update
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read == False)
            .values(read=True)
        )
        result = await db.execute(stmt)
        await db.commit()
        return {"count": result.rowcount}


@app.get("/notifications/unread-count")
async def unread_count(user_id: str):
    """Get count of unread notifications for a user."""
    async with get_db_session() as db:
        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.read == False,
            )
        )
        count = result.scalar() or 0
        return {"count": count}


@app.get("/health")
async def health():
    return {"status": "ok"}

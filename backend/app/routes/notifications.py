"""Notification proxy routes — forward requests to notification-svc via Dapr service invocation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from app.database import get_session
from app.dependencies import get_current_user
from app.models import Task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

DAPR_HTTP_PORT = 3500
NOTIFICATION_APP_ID = "notification-svc"
DAPR_INVOKE_URL = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/invoke/{NOTIFICATION_APP_ID}/method"


async def _invoke_notification_svc(method: str, params: dict | None = None, http_method: str = "GET", json_body: dict | None = None):
    """Invoke notification service via Dapr service invocation."""
    url = f"{DAPR_INVOKE_URL}/{method}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if http_method == "GET":
                resp = await client.get(url, params=params)
            elif http_method == "POST":
                resp = await client.post(url, params=params, json=json_body)
            elif http_method == "PATCH":
                resp = await client.patch(url, params=params, json=json_body)
            else:
                resp = await client.request(http_method, url, params=params, json=json_body)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Notification service error")
    except Exception:
        logger.error("Failed to invoke notification service", exc_info=True)
        raise HTTPException(status_code=503, detail="Notification service unavailable")


@router.get("")
async def list_notifications(
    user_id: str = Depends(get_current_user),
    unread_only: bool = Query(False),
    limit: int = Query(20, le=50),
    cursor: Optional[str] = Query(None),
):
    """List notifications for current user (proxied to notification-svc)."""
    params = {"user_id": user_id, "unread_only": str(unread_only).lower(), "limit": str(limit)}
    if cursor:
        params["cursor"] = cursor
    return await _invoke_notification_svc("notifications", params=params)


@router.patch("/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    user_id: str = Depends(get_current_user),
):
    """Mark a notification as read (proxied to notification-svc)."""
    return await _invoke_notification_svc(
        f"notifications/{notif_id}/read",
        params={"user_id": user_id},
        http_method="PATCH",
    )


@router.post("/read-all")
async def mark_all_read(
    user_id: str = Depends(get_current_user),
):
    """Mark all notifications as read (proxied to notification-svc)."""
    return await _invoke_notification_svc(
        "notifications/read-all",
        params={"user_id": user_id},
        http_method="POST",
    )


@router.get("/unread-count")
async def unread_count(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Count tasks with upcoming reminders (due within 24 hours, not yet notified)."""
    cutoff = datetime.now(timezone.utc) + timedelta(hours=24)
    result = await db.execute(
        select(func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.due_date <= cutoff,
            Task.due_date >= datetime.now(timezone.utc),
            Task.completed == False,
            Task.reminder_notified_at == None,
        )
    )
    return {"count": result.scalar() or 0}

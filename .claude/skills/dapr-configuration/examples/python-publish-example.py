"""
Todo App — Dapr Pub/Sub Publisher Example (FastAPI + httpx)

Publishes task lifecycle events to Dapr Pub/Sub topics.
Integrate into your FastAPI route handlers.

Requirements:
    pip install httpx

Environment:
    DAPR_HTTP_PORT (default: 3500) — set automatically by Dapr sidecar
"""

import os
from datetime import datetime, timezone
from uuid import UUID

import httpx

DAPR_HTTP_PORT = os.getenv("DAPR_HTTP_PORT", "3500")
DAPR_BASE_URL = f"http://localhost:{DAPR_HTTP_PORT}"
PUBSUB_NAME = "pubsub"


# ---------------------------------------------------------------------------
# Core publish function
# ---------------------------------------------------------------------------

async def publish_event(topic: str, event_type: str, data: dict) -> None:
    """Publish a CloudEvent to a Dapr Pub/Sub topic."""
    payload = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{DAPR_BASE_URL}/v1.0/publish/{PUBSUB_NAME}/{topic}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5.0,
        )
        resp.raise_for_status()


# ---------------------------------------------------------------------------
# Task event publishers
# ---------------------------------------------------------------------------

async def publish_task_created(task_id: UUID, title: str, user_id: str) -> None:
    await publish_event("task-events", "task.created", {
        "task_id": str(task_id),
        "title": title,
        "user_id": user_id,
    })
    # Also publish to real-time sync topic
    await publish_event("task-updates", "task.created", {
        "task_id": str(task_id),
        "title": title,
    })


async def publish_task_completed(task_id: UUID, title: str, user_id: str) -> None:
    await publish_event("task-events", "task.completed", {
        "task_id": str(task_id),
        "title": title,
        "user_id": user_id,
    })
    await publish_event("task-updates", "task.completed", {
        "task_id": str(task_id),
    })


async def publish_task_deleted(task_id: UUID, user_id: str) -> None:
    await publish_event("task-events", "task.deleted", {
        "task_id": str(task_id),
        "user_id": user_id,
    })
    await publish_event("task-updates", "task.deleted", {
        "task_id": str(task_id),
    })


# ---------------------------------------------------------------------------
# Reminder publishers (called by cron handler)
# ---------------------------------------------------------------------------

async def publish_overdue_reminder(task_id: UUID, title: str, due_date: str) -> None:
    await publish_event("reminders", "reminder.overdue", {
        "task_id": str(task_id),
        "title": title,
        "due_date": due_date,
    })


async def publish_due_soon_reminder(task_id: UUID, title: str, due_date: str) -> None:
    await publish_event("reminders", "reminder.due-soon", {
        "task_id": str(task_id),
        "title": title,
        "due_date": due_date,
    })


# ---------------------------------------------------------------------------
# State store helpers
# ---------------------------------------------------------------------------

STATE_STORE = "statestore"


async def save_state(key: str, value: dict, ttl_seconds: int | None = None) -> None:
    """Save a key-value pair to the Dapr state store."""
    item: dict = {"key": key, "value": value}
    if ttl_seconds:
        item["metadata"] = {"ttlInSeconds": str(ttl_seconds)}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{DAPR_BASE_URL}/v1.0/state/{STATE_STORE}",
            json=[item],
            timeout=5.0,
        )
        resp.raise_for_status()


async def get_state(key: str) -> dict | None:
    """Retrieve a value from the Dapr state store."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{DAPR_BASE_URL}/v1.0/state/{STATE_STORE}/{key}",
            timeout=5.0,
        )
        if resp.status_code == 204:
            return None
        resp.raise_for_status()
        return resp.json()


async def delete_state(key: str) -> None:
    """Delete a key from the Dapr state store."""
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{DAPR_BASE_URL}/v1.0/state/{STATE_STORE}/{key}",
            timeout=5.0,
        )
        resp.raise_for_status()


# ---------------------------------------------------------------------------
# Service invocation helper
# ---------------------------------------------------------------------------

async def invoke_service(app_id: str, method: str, data: dict | None = None) -> dict:
    """Invoke a method on another Dapr service."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{DAPR_BASE_URL}/v1.0/invoke/{app_id}/method/{method}",
            json=data or {},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Usage in FastAPI route (example)
# ---------------------------------------------------------------------------
#
# from fastapi import APIRouter
# from .dapr_publish import publish_task_created
#
# router = APIRouter()
#
# @router.post("/api/todos")
# async def create_todo(payload: CreateTodoRequest):
#     todo = await save_todo_to_db(payload)
#     await publish_task_created(todo.id, todo.title, todo.user_id)
#     return todo

"""Dapr pub/sub publish helper with retry logic and state store access."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.events.schemas import TaskEventData, TaskUpdateData, task_to_snapshot
from app.models import TaskEvent, ProcessedEvent

logger = logging.getLogger(__name__)

DAPR_HTTP_PORT = 3500
DAPR_BASE_URL = f"http://localhost:{DAPR_HTTP_PORT}"
PUBSUB_NAME = "pubsub"
STATE_STORE = "statestore"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 2.0, 4.0]  # exponential backoff


async def dapr_publish(topic: str, event_type: str, data: dict[str, Any]) -> None:
    """Publish an event to a Dapr pub/sub topic with retry logic.

    Retries up to 3 times with exponential backoff (1s, 2s, 4s)
    to guarantee at-least-once delivery (FR-004).
    """
    url = f"{DAPR_BASE_URL}/v1.0/publish/{PUBSUB_NAME}/{topic}"
    payload = data

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "ce-type": event_type,
                        "ce-source": "backend-api",
                        "ce-id": str(uuid.uuid4()),
                        "ce-specversion": "1.0",
                    },
                )
                resp.raise_for_status()
            logger.info(
                "Published event",
                extra={"topic": topic, "event_type": event_type, "task_id": data.get("task_id")},
            )
            return
        except Exception:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    "Publish failed, retrying",
                    extra={"topic": topic, "attempt": attempt + 1, "delay": delay},
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "Publish failed after all retries",
                    extra={"topic": topic, "event_type": event_type},
                    exc_info=True,
                )


async def publish_task_event(
    event_type: str,
    task,
    user_id: str,
    db: AsyncSession,
    changed_fields: dict[str, Any] | None = None,
) -> None:
    """Persist task event to DB AND publish to task-events and task-updates topics.

    This is fire-and-forget via asyncio.create_task — never blocks user requests.
    For delete events, task snapshot is set to null per events.yaml contract.
    """
    task_snapshot = task_to_snapshot(task) if event_type != "deleted" else None
    task_id_str = str(task.id)

    # 1. Persist to task_event table (audit trail)
    task_event = TaskEvent(
        event_type=event_type,
        task_id=task.id,
        user_id=user_id,
        timestamp=datetime.utcnow(),
        data=task_snapshot or {"task_id": task_id_str},
        changed_fields=changed_fields,
        event_source="api",
    )
    db.add(task_event)
    await db.commit()

    # 2. Publish to task-events (full event for processing)
    task_event_data = TaskEventData(
        event_type=event_type,
        task_id=task_id_str,
        user_id=user_id,
        task=task_snapshot,
        changed_fields=changed_fields,
    )

    # 3. Publish to task-updates (lightweight for SSE sync)
    task_update_data = TaskUpdateData(
        change_type=event_type,
        task_id=task_id_str,
        user_id=user_id,
        changed_fields=list((changed_fields or {}).keys()),
        timestamp=datetime.utcnow().isoformat(),
    )

    # Fire-and-forget publishing — never block the response
    asyncio.create_task(
        dapr_publish("task-events", f"task.{event_type}", task_event_data.to_dict())
    )
    asyncio.create_task(
        dapr_publish("task-updates", "sync.task-changed", task_update_data.to_dict())
    )


# --- Idempotency Helper (T017) ---


async def check_and_mark_processed(
    event_id: str, consumer_group: str, db: AsyncSession
) -> bool:
    """Check if an event was already processed. Returns True if already processed.

    Uses the processed_event table for consumer idempotency.
    """
    result = await db.execute(
        select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return True

    # Mark as processed
    record = ProcessedEvent(
        event_id=event_id,
        consumer_group=consumer_group,
        processed_at=datetime.utcnow(),
    )
    db.add(record)
    await db.commit()
    return False


# --- Dapr State Store Helpers (T018) ---


async def get_state(key: str) -> Any | None:
    """Get value from Dapr state store."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{DAPR_BASE_URL}/v1.0/state/{STATE_STORE}/{key}")
            if resp.status_code == 200 and resp.text:
                return resp.json()
            return None
    except Exception:
        logger.warning("Failed to get state", extra={"key": key}, exc_info=True)
        return None


async def save_state(key: str, value: Any, ttl: int | None = None) -> None:
    """Save value to Dapr state store with optional TTL in seconds."""
    try:
        state_item: dict[str, Any] = {"key": key, "value": value}
        if ttl:
            state_item["metadata"] = {"ttlInSeconds": str(ttl)}
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{DAPR_BASE_URL}/v1.0/state/{STATE_STORE}",
                json=[state_item],
            )
            resp.raise_for_status()
    except Exception:
        logger.warning("Failed to save state", extra={"key": key}, exc_info=True)


async def delete_state(key: str) -> None:
    """Delete a key from Dapr state store."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.delete(f"{DAPR_BASE_URL}/v1.0/state/{STATE_STORE}/{key}")
            resp.raise_for_status()
    except Exception:
        logger.warning("Failed to delete state", extra={"key": key}, exc_info=True)

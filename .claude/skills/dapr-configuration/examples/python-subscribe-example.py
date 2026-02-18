"""
Todo App — Dapr Pub/Sub Subscriber & Cron Handler Example (FastAPI)

Handles incoming events from Dapr Pub/Sub subscriptions and cron bindings.
Mount this router in your FastAPI app.

Requirements:
    pip install fastapi httpx

The Dapr sidecar delivers events as HTTP POST requests to your app.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dapr"])


# ---------------------------------------------------------------------------
# Programmatic subscription registration
# ---------------------------------------------------------------------------
# Dapr calls GET /dapr/subscribe on startup to discover subscriptions.
# Alternative: use declarative YAML subscriptions (see subscription.yaml.template).

@router.get("/dapr/subscribe")
async def dapr_subscribe():
    """Register Pub/Sub subscriptions with Dapr sidecar."""
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task-events",
            "routes": {
                "rules": [
                    {"match": 'event.type == "task.created"', "path": "/events/task/created"},
                    {"match": 'event.type == "task.updated"', "path": "/events/task/updated"},
                    {"match": 'event.type == "task.deleted"', "path": "/events/task/deleted"},
                    {"match": 'event.type == "task.completed"', "path": "/events/task/completed"},
                ],
                "default": "/events/task-events",
            },
        },
        {
            "pubsubname": "pubsub",
            "topic": "reminders",
            "route": "/events/reminders",
        },
        {
            "pubsubname": "pubsub",
            "topic": "task-updates",
            "route": "/events/task-updates",
        },
    ]


# ---------------------------------------------------------------------------
# Task event handlers
# ---------------------------------------------------------------------------

@router.post("/events/task-events")
async def handle_task_event_default(request: Request):
    """Catch-all handler for task events (no content-based routing match)."""
    event = await request.json()
    data = event.get("data", {})
    logger.info("Task event (default): type=%s data=%s", event.get("type"), data)
    return {"status": "SUCCESS"}


@router.post("/events/task/created")
async def handle_task_created(request: Request):
    """Handle task.created events."""
    event = await request.json()
    data = event.get("data", {})
    task_id = data.get("task_id")
    title = data.get("title")
    logger.info("Task created: id=%s title=%s", task_id, title)

    # Example: Update search index, notify watchers, etc.
    # await update_search_index(task_id)
    # await notify_watchers(task_id, "created")

    return {"status": "SUCCESS"}


@router.post("/events/task/updated")
async def handle_task_updated(request: Request):
    """Handle task.updated events."""
    event = await request.json()
    data = event.get("data", {})
    logger.info("Task updated: id=%s", data.get("task_id"))
    return {"status": "SUCCESS"}


@router.post("/events/task/completed")
async def handle_task_completed(request: Request):
    """Handle task.completed events."""
    event = await request.json()
    data = event.get("data", {})
    task_id = data.get("task_id")
    logger.info("Task completed: id=%s", task_id)

    # Example: Check if part of a recurring task and schedule next
    # await maybe_schedule_next_recurrence(task_id)

    return {"status": "SUCCESS"}


@router.post("/events/task/deleted")
async def handle_task_deleted(request: Request):
    """Handle task.deleted events."""
    event = await request.json()
    data = event.get("data", {})
    logger.info("Task deleted: id=%s", data.get("task_id"))
    return {"status": "SUCCESS"}


# ---------------------------------------------------------------------------
# Reminder event handlers
# ---------------------------------------------------------------------------

@router.post("/events/reminders")
async def handle_reminder(request: Request):
    """Handle reminder events (overdue, due-soon)."""
    event = await request.json()
    data = event.get("data", {})
    reminder_type = event.get("type", "unknown")
    task_id = data.get("task_id")
    logger.info("Reminder: type=%s task_id=%s", reminder_type, task_id)

    # Example: Send push notification, email, or in-app alert
    # await send_notification(task_id, reminder_type)

    return {"status": "SUCCESS"}


# ---------------------------------------------------------------------------
# Real-time task updates (bridge to SSE for frontend)
# ---------------------------------------------------------------------------

@router.post("/events/task-updates")
async def handle_task_update(request: Request):
    """Handle real-time task update events for client sync."""
    event = await request.json()
    data = event.get("data", {})
    logger.info("Task update for clients: %s", data)

    # Example: Push to SSE connections or WebSocket clients
    # await sse_manager.broadcast(data)

    return {"status": "SUCCESS"}


# ---------------------------------------------------------------------------
# Cron binding handlers
# ---------------------------------------------------------------------------
# Dapr calls POST /<binding-name> at the configured schedule.
# The binding name matches the component metadata name.

@router.post("/cron-overdue-check")
async def cron_check_overdue(request: Request):
    """Called by Dapr cron binding every 5 minutes.

    Finds overdue tasks and publishes reminder events.
    """
    logger.info("Cron: checking for overdue tasks at %s", datetime.now(timezone.utc))

    # Import your publish helper
    # from .dapr_publish import publish_overdue_reminder
    #
    # overdue_tasks = await db.find_overdue_tasks()
    # for task in overdue_tasks:
    #     await publish_overdue_reminder(
    #         task_id=task.id,
    #         title=task.title,
    #         due_date=task.due_date.isoformat(),
    #     )
    # logger.info("Published %d overdue reminders", len(overdue_tasks))

    return {"status": "SUCCESS"}


@router.post("/cron-recurring-tasks")
async def cron_process_recurring(request: Request):
    """Called by Dapr cron binding every hour.

    Generates next occurrences for recurring tasks whose current
    occurrence has been completed or whose due date has passed.
    """
    logger.info("Cron: processing recurring tasks at %s", datetime.now(timezone.utc))

    # from .recurring import generate_next_occurrences
    # count = await generate_next_occurrences()
    # logger.info("Generated %d recurring task instances", count)

    return {"status": "SUCCESS"}


# ---------------------------------------------------------------------------
# Health check (Dapr readiness)
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    """Health endpoint for Dapr readiness probe."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# Mount in your FastAPI app:
#
# from fastapi import FastAPI
# from .dapr_subscribe import router as dapr_router
#
# app = FastAPI()
# app.include_router(dapr_router)
# ---------------------------------------------------------------------------

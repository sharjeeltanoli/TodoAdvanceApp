# Data Model: Event-Driven Todo System

**Feature**: 005-event-driven | **Date**: 2026-02-17

## Existing Entities (Phase 1 + Phase 4)

### Task (existing — no schema changes)
```
id: UUID (PK)
user_id: String (indexed)
title: String (max 255)
description: String | null (max 2000)
completed: Boolean (default false)
priority: String (high/medium/low, default medium)
tags: JSONB (array, max 10)
due_date: DateTime | null
recurrence_pattern: JSONB | null
  └─ frequency: daily | weekly | monthly
  └─ interval: int
  └─ next_due: DateTime
reminder_minutes: int | null (15, 60, 1440)
snoozed_until: DateTime | null
reminder_notified_at: DateTime | null
parent_task_id: UUID | null (FK → task.id)
created_at: DateTime
updated_at: DateTime
```

## New Entities

### TaskEvent (PostgreSQL table — audit trail)

Persists every task change for audit trail (User Story 4).

```sql
CREATE TABLE task_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(20) NOT NULL,  -- created, updated, deleted, completed
    task_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    data JSONB NOT NULL,              -- full task state at time of event
    changed_fields JSONB,             -- for updates: {"title": {"old": "x", "new": "y"}}
    event_source VARCHAR(50) DEFAULT 'api',  -- api, scheduler, recurring

    CONSTRAINT valid_event_type CHECK (event_type IN ('created', 'updated', 'deleted', 'completed'))
);

CREATE INDEX idx_task_event_task_id ON task_event(task_id);
CREATE INDEX idx_task_event_user_id ON task_event(user_id);
CREATE INDEX idx_task_event_timestamp ON task_event(timestamp DESC);
```

**Relationships**:
- `task_id` references `task.id` (soft reference — task may be deleted)
- `user_id` matches `task.user_id` for isolation

### Notification (PostgreSQL table)

Stores in-app notifications for users.

```sql
CREATE TABLE notification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    type VARCHAR(30) NOT NULL,        -- reminder_upcoming, reminder_overdue, task_recurring
    title VARCHAR(255) NOT NULL,
    body TEXT,
    task_id UUID,                     -- reference to related task
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT valid_notification_type CHECK (
        type IN ('reminder_upcoming', 'reminder_overdue', 'task_recurring')
    )
);

CREATE INDEX idx_notification_user_id ON notification(user_id);
CREATE INDEX idx_notification_user_unread ON notification(user_id, read) WHERE read = false;
```

### ProcessedEvent (PostgreSQL table — idempotency)

Tracks processed event IDs for consumer idempotency.

```sql
CREATE TABLE processed_event (
    event_id VARCHAR(255) PRIMARY KEY,  -- CloudEvents ID
    consumer_group VARCHAR(100) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- TTL cleanup: DELETE WHERE processed_at < now() - interval '7 days'
CREATE INDEX idx_processed_event_age ON processed_event(processed_at);
```

## Event Schemas (CloudEvents via Dapr)

### TaskEvent (published to `task-events` topic)

```json
{
  "specversion": "1.0",
  "id": "uuid-auto-generated-by-dapr",
  "source": "backend-api",
  "type": "task.created",
  "time": "2026-02-17T10:30:00Z",
  "data": {
    "event_type": "created",
    "task_id": "uuid",
    "user_id": "user-123",
    "task": {
      "id": "uuid",
      "title": "Buy groceries",
      "completed": false,
      "priority": "medium",
      "tags": ["shopping"],
      "due_date": "2026-02-18T09:00:00Z",
      "recurrence_pattern": null
    },
    "changed_fields": null
  }
}
```

### ReminderEvent (published to `reminders` topic)

```json
{
  "specversion": "1.0",
  "type": "reminder.upcoming",
  "data": {
    "reminder_type": "upcoming",
    "task_id": "uuid",
    "user_id": "user-123",
    "title": "Buy groceries",
    "due_date": "2026-02-18T09:00:00Z",
    "link": "/dashboard?task=uuid"
  }
}
```

### TaskUpdate (published to `task-updates` topic)

Lightweight payload for real-time client sync.

```json
{
  "specversion": "1.0",
  "type": "sync.task-changed",
  "data": {
    "change_type": "updated",
    "task_id": "uuid",
    "user_id": "user-123",
    "changed_fields": ["title", "completed"],
    "timestamp": "2026-02-17T10:30:00Z"
  }
}
```

## State Store Keys (Redis via Dapr)

| Key Pattern | Value | TTL | Purpose |
|-------------|-------|-----|---------|
| `reminder:{task_id}:{window}` | `{"sent": true}` | 3600s | Dedup reminders within window |
| `conversation:{id}` | Last N messages JSON | 3600s | Conversation cache |
| `user-prefs:{user_id}` | Preferences JSON | 86400s | User settings cache |
| `sse-clients:{user_id}` | Connection count | 60s | SSE connection tracking |

## Database Migration

New tables (`task_event`, `notification`, `processed_event`) are additive — no changes to existing tables. Migration can be applied independently.

**Alembic migration**: `alembic revision --autogenerate -m "add event-driven tables"`

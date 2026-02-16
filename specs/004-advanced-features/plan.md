# Implementation Plan: Enhanced Task Management

**Branch**: `004-advanced-features` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-advanced-features/spec.md`

## Summary

Extend the existing todo app with priority levels, tags, due dates, search/filter/sort, recurring tasks, and browser reminders. The approach adds new columns to the `task` table via Alembic migration, extends FastAPI models and endpoints with query parameters, creates new frontend UI components (priority selector, tag input, date picker, filter bar, search), and adds a background scheduler for recurring task generation and a client-side reminder system using the Browser Notification API.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI 0.115.8, SQLModel, Next.js 16.1.6, React 19, Tailwind CSS 4
**Storage**: Neon Serverless PostgreSQL (shared), Alembic for migrations
**Testing**: pytest (backend), manual/browser (frontend — no test framework installed yet)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (monorepo: `frontend/` + `backend/`)
**Performance Goals**: Search/filter/sort < 1s for 500 tasks per user; recurring generation within 5 min
**Constraints**: No Kafka (Phase 5B), backward-compatible with existing tasks, browser notifications only when app is open
**Scale/Scope**: Extends existing 6 REST endpoints + 6 MCP tools, adds ~8 new UI components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Spec-Driven Development | PASS | spec.md created, plan.md in progress, tasks.md will follow |
| II. Monorepo Structure | PASS | Changes in `frontend/` and `backend/` per convention |
| III. Stateless Services | PASS | All new state (priority, tags, due dates, recurrence) persisted in PostgreSQL. Recurring task scheduler reads DB state — no in-memory caches |
| IV. Event-Driven Architecture | WAIVER | Spec explicitly defers Kafka to Phase 5B. Recurring task generation uses a simple async background scheduler (APScheduler) instead. This is justified: the scheduler only creates tasks locally — no inter-service communication needed |
| V. User Isolation | PASS | All queries filtered by `user_id`. Tags are user-scoped. Reminders are per-user |
| VI. MCP Protocol | PASS | MCP tools will be extended with new fields (priority, tags, due_date) |

## Project Structure

### Documentation (this feature)

```text
specs/004-advanced-features/
├── plan.md              # This file
├── research.md          # Phase 0: Technology research
├── data-model.md        # Phase 1: Entity design
├── quickstart.md        # Phase 1: Developer setup
├── contracts/
│   └── api.yaml         # Phase 1: OpenAPI contract
└── tasks.md             # Phase 2: Task breakdown (via /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models.py                 # MODIFY: Add priority, tags, due_date, recurrence fields + new models
│   ├── routes/
│   │   └── todos.py              # MODIFY: Add query params (search, filter, sort) + new endpoints
│   └── scheduler.py              # NEW: APScheduler for recurring task generation
├── alembic/
│   └── versions/
│       └── 004_add_advanced_fields.py  # NEW: Migration for new columns + tables
└── mcp_server/
    └── server.py                 # MODIFY: Extend MCP tools with new fields

frontend/
├── src/
│   ├── components/
│   │   ├── tasks/
│   │   │   ├── task-list.tsx     # MODIFY: Add search bar, filter bar, sort controls
│   │   │   ├── task-item.tsx     # MODIFY: Show priority badge, tags, due date, description preview
│   │   │   └── task-form.tsx     # MODIFY: Add priority selector, tag input, date picker, recurrence toggle
│   │   └── ui/
│   │       ├── priority-badge.tsx    # NEW: Color-coded priority indicator
│   │       ├── tag-input.tsx         # NEW: Tag chip input with autocomplete
│   │       ├── date-picker.tsx       # NEW: Date picker using native input[type=date]
│   │       ├── filter-bar.tsx        # NEW: Combined filter controls
│   │       ├── sort-select.tsx       # NEW: Sort dropdown
│   │       └── search-input.tsx      # NEW: Debounced search bar
│   ├── lib/
│   │   └── notifications.ts     # NEW: Browser Notification API wrapper
│   └── app/
│       └── dashboard/
│           └── actions.ts        # MODIFY: Add new fields to create/update, add search/filter params
└── package.json                  # MODIFY: Add date-fns (date formatting)
```

**Structure Decision**: Extends existing monorepo structure. All new backend logic in existing `app/` package. New frontend components in existing `components/` directory. No new top-level directories needed.

## Architecture Decisions

### D1: Tags as JSON Array (not separate table)

Store tags as a PostgreSQL `JSONB` array column on the `task` table rather than a separate `tag` / `task_tag` many-to-many table.

**Rationale**: Tags are simple strings (max 10 per task). A JSONB array avoids JOIN overhead, simplifies the API (tags travel with the task), and PostgreSQL GIN indexes on JSONB support efficient containment queries (`@>` operator). The 10-tag limit keeps the array small.

**Trade-off**: Cannot query "all tasks with tag X across all users" efficiently. But per the spec, tags are user-scoped and only queried within a user's task list (always filtered by `user_id` first, then tag containment), which is well-served by a GIN index.

### D2: Priority as Text with CHECK Constraint (not native PG enum)

Use a PostgreSQL `text` column with CHECK constraint (`high`, `medium`, `low`) rather than a native PG enum type.

**Rationale**: PG native enums are difficult to alter (adding/removing values requires migrations with type changes). A text column with a CHECK constraint is functionally equivalent, easier to migrate, and works well with SQLModel/Pydantic enum validation on the Python side.

### D3: Native HTML Date Input (no external date picker library)

Use `<input type="date">` for due date selection instead of adding a third-party date picker library (react-day-picker, etc.).

**Rationale**: The native date input is well-supported in all modern browsers, requires zero bundle size increase, and meets the spec requirements. If richer UX is needed later, a library can be added without breaking changes.

### D4: APScheduler for Recurring Tasks (not Kafka/Celery)

Use APScheduler (AsyncIO scheduler) running inside the FastAPI process for recurring task generation.

**Rationale**: The spec explicitly defers Kafka to Phase 5B. APScheduler is lightweight, requires no additional infrastructure, and runs in-process. It checks every 5 minutes for recurring tasks that need new instances. When Kafka is introduced in Phase 5B, the scheduler can be replaced with an event-driven consumer.

### D5: Client-Side Polling for Reminders (not WebSocket/SSE)

Use a frontend polling mechanism (check every 60 seconds) to fetch upcoming reminders rather than WebSocket or Server-Sent Events.

**Rationale**: Reminders only need minute-level precision (per SC-006). Polling every 60s is simple, requires no additional backend infrastructure, and works reliably. The polling fetches a lightweight "upcoming reminders" endpoint. When Phase 5B adds real-time features, this can be upgraded to WebSocket/SSE.

## Implementation Phases

### Phase A: Database & Models (P1 foundation)

1. Create Alembic migration `004_add_advanced_fields.py`:
   - Add `priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('high','medium','low'))` to `task`
   - Add `tags JSONB NOT NULL DEFAULT '[]'::jsonb` to `task`
   - Add `due_date TIMESTAMPTZ NULL` to `task`
   - Add `description` already exists — no change needed
   - Add `recurrence_pattern JSONB NULL` to `task` (stores `{frequency, interval, next_due}`)
   - Add `reminder_minutes INTEGER NULL` to `task` (lead time: 15, 60, 1440)
   - Add `snoozed_until TIMESTAMPTZ NULL` to `task` (set by snooze endpoint; reminders suppressed until this time)
   - Add `reminder_notified_at TIMESTAMPTZ NULL` to `task` (tracks when notification was last shown; prevents duplicates)
   - Add `parent_task_id UUID NULL REFERENCES task(id) ON DELETE SET NULL` to `task`
   - Create indexes:
     - `ix_task_user_priority` on `(user_id, priority)`
     - `ix_task_user_due` on `(user_id, due_date)` WHERE `due_date IS NOT NULL`
     - `ix_task_user_tags` GIN index on `(tags)` WHERE `user_id` (partial GIN not possible, use composite)
   - Existing tasks get `priority='medium'`, `tags='[]'`, `due_date=NULL`

2. Update `backend/app/models.py`:
   - Add `priority`, `tags`, `due_date`, `recurrence_pattern`, `reminder_minutes`, `snoozed_until`, `reminder_notified_at`, `parent_task_id` to `Task`
   - Add Python `enum.Enum` for `Priority` (high, medium, low)
   - Update `TaskCreate`, `TaskUpdate`, `TaskResponse` with new fields
   - Add `RecurrencePattern` Pydantic model (frequency, interval, next_due)

### Phase B: API Endpoints (P1 + P2)

1. Extend `GET /todos` with query parameters:
   - `search: str | None` — case-insensitive ILIKE on title + description
   - `status: str | None` — "pending" or "completed"
   - `priority: str | None` — "high", "medium", or "low"
   - `tag: str | None` — filter tasks containing this tag
   - `sort_by: str = "created_at"` — one of: "created_at", "due_date", "priority"
   - `sort_dir: str = "desc"` — "asc" or "desc"

2. Extend `POST /todos` and `PUT /todos/{id}`:
   - Accept `priority`, `tags`, `due_date`, `recurrence_pattern`, `reminder_minutes`
   - Validate tags (max 10, lowercase normalization)

3. Add `GET /todos/tags` — return distinct tags for current user (for autocomplete)

4. Add `POST /todos/{id}/snooze` — postpone reminder by 15 minutes

### Phase C: Frontend UI (P1 + P2)

1. Install `date-fns` for date formatting/relative time display
2. Create new UI components:
   - `PriorityBadge` — colored badge (red/yellow/green for high/medium/low)
   - `TagInput` — chip input with autocomplete dropdown
   - `DatePicker` — native `<input type="date">` wrapper with clear button
   - `FilterBar` — status, priority, tag filter dropdowns + clear all
   - `SortSelect` — sort-by dropdown with direction toggle
   - `SearchInput` — debounced text input with search icon
3. Update `TaskForm` — add priority selector, tag input, date picker
4. Update `TaskItem` — show priority badge, tag chips, due date (with overdue indicator)
5. Update `TaskList` — integrate search bar, filter bar, sort controls above task list
6. Update `actions.ts` — pass new fields in create/update, pass query params to list

### Phase D: Recurring Tasks (P3)

1. Add `APScheduler` to backend dependencies
2. Create `backend/app/scheduler.py`:
   - On startup, register a job that runs every 5 minutes
   - Query tasks where `recurrence_pattern IS NOT NULL` and `next_due <= NOW()`
   - For each, create a new task instance (copy title, description, priority, tags)
   - Update `next_due` based on frequency
3. Integrate scheduler startup in `backend/app/main.py`
4. Add recurrence toggle UI in `TaskForm` (frequency selector: daily/weekly/monthly)
5. Show recurrence indicator on `TaskItem`

### Phase E: Reminders (P3)

1. Create `frontend/src/lib/notifications.ts`:
   - `requestPermission()` — wraps `Notification.requestPermission()`
   - `showNotification(title, body)` — creates browser notification
   - `checkReminders()` — polls backend for upcoming reminders
2. Add `GET /todos/reminders` endpoint — return tasks where `due_date - reminder_minutes <= NOW()`, not completed, and (`reminder_notified_at IS NULL` or `snoozed_until IS NOT NULL AND snoozed_until <= NOW()`)
3. Frontend: start polling on dashboard mount, show notifications for due reminders
4. After showing notification, `PATCH` the task to set `reminder_notified_at = NOW()` to prevent duplicate notifications
5. Snooze: call `POST /todos/{id}/snooze` which sets `snoozed_until = NOW() + 15 min` and clears `reminder_notified_at` (so it re-fires after snooze period)

### Phase F: MCP Tools Update

1. Extend `add_task` tool with `priority`, `tags`, `due_date` parameters
2. Extend `list_tasks` tool with `search`, `priority`, `tag` filter parameters
3. Extend `update_task` tool with new fields
4. Add `task_dict` serialization for new fields
5. Mirror the inline `Task` model in MCP server with new columns

## Risk Analysis

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Migration breaks existing tasks | HIGH | Default values ensure backward compatibility; test migration on staging first |
| APScheduler missed jobs (process restart) | MEDIUM | Scheduler checks `next_due <= NOW()` on startup — catches up on missed intervals (but only creates one instance, not backfill) |
| Browser notification permission denied | LOW | Graceful fallback: show in-app badge/toast instead of system notification |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| IV. Event-Driven (Kafka waiver) | Spec defers Kafka to Phase 5B; recurring tasks are local-only operations | Kafka would add infrastructure complexity with no cross-service benefit at this stage |

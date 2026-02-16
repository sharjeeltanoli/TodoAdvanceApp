# Research: Enhanced Task Management (004-advanced-features)

**Date**: 2026-02-16
**Feature**: [spec.md](./spec.md)

## R1: Tag Storage Strategy

**Decision**: JSONB array column on the `task` table
**Rationale**: Tags are simple lowercase strings, max 10 per task. A JSONB array avoids JOIN overhead, keeps the API simple (tags travel with the task), and PostgreSQL GIN indexes support efficient containment queries (`tags @> '["work"]'::jsonb`).
**Alternatives considered**:
- Separate `tag` + `task_tag` tables (normalized): More flexible but adds JOINs to every task query. Overkill for max 10 string tags per task.
- PostgreSQL `TEXT[]` array: Similar to JSONB but less flexible for querying. GIN index works on both, but JSONB has richer operator support.

## R2: Priority Storage

**Decision**: TEXT column with CHECK constraint
**Rationale**: PostgreSQL native enums (`CREATE TYPE`) are difficult to alter — adding values requires `ALTER TYPE ... ADD VALUE` which cannot run inside a transaction. A TEXT column with `CHECK (priority IN ('high','medium','low'))` is functionally equivalent and easier to migrate.
**Alternatives considered**:
- Native PG enum: Immutable after creation (can add values but not remove). Migration headaches.
- Integer column (1/2/3): Works but loses readability in raw queries and requires mapping layer.

## R3: Date Picker Library

**Decision**: Native `<input type="date">` (no library)
**Rationale**: All target browsers (Chrome, Firefox, Edge, Safari 14.1+) support native date inputs. Zero bundle size impact. Meets spec requirements (select a date, clear a date). The native picker UI is consistent with OS conventions.
**Alternatives considered**:
- react-day-picker + date-fns: Rich UI but adds ~30KB to bundle. Not justified for a simple date field.
- react-datepicker: Popular but heavier. Would need to be styled to match Tailwind design.

## R4: Recurring Task Scheduler

**Decision**: APScheduler (AsyncIO scheduler) running in-process with FastAPI
**Rationale**: Lightweight, no additional infrastructure needed. Runs an interval job every 5 minutes to check for recurring tasks needing new instances. The constitution defers Kafka to Phase 5B, and recurring task generation is a local operation (no inter-service communication).
**Alternatives considered**:
- Celery + Redis: Production-grade but adds Redis dependency and worker process. Over-engineered for this phase.
- Cron job (system-level): Requires external process management. Doesn't integrate with the async Python ecosystem.
- PostgreSQL `pg_cron`: Keeps logic in DB but harder to test and debug. Neon Serverless may not support extensions.

## R5: Reminder Delivery

**Decision**: Client-side polling (60s interval) + Browser Notification API
**Rationale**: Reminders need minute-level precision (SC-006: within 1 minute). Polling every 60 seconds is simple and meets the requirement. No WebSocket/SSE infrastructure needed. The Notification API is supported by all modern browsers.
**Alternatives considered**:
- WebSocket push: Real-time but adds connection management complexity. Deferred to Phase 5B.
- Service Worker push notifications: Works offline but requires push subscription server. Overkill for "app must be open" requirement.
- Server-Sent Events: Simpler than WebSocket but still requires persistent connection. Not justified for 60s polling.

## R6: Search Implementation

**Decision**: PostgreSQL `ILIKE` with `%keyword%` pattern on title + description
**Rationale**: For the expected scale (≤500 tasks per user, per SC-002), ILIKE is fast enough without full-text search. The query is always user-scoped (indexed by `user_id`), so the ILIKE scan runs over a small subset.
**Alternatives considered**:
- PostgreSQL `tsvector` + `tsquery` (full-text search): More powerful but adds complexity (maintaining tsvector columns, GIN index). Not needed for simple keyword matching at this scale.
- Application-level search (frontend filter): Would require loading all tasks to the client. Doesn't work well with pagination.

## R7: Frontend Date Formatting

**Decision**: Add `date-fns` as a dependency for date display utilities
**Rationale**: Need relative time display ("due in 3 days", "overdue by 2 hours"), date formatting, and date comparison. `date-fns` is tree-shakeable and lightweight (~2KB for used functions). Already a standard choice in the React ecosystem.
**Alternatives considered**:
- Native `Intl.DateTimeFormat`: Handles formatting but not relative time or date arithmetic.
- dayjs: Similar to date-fns but mutable API. date-fns is more idiomatic with functional patterns.

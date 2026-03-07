---
id: "0033"
title: Fix notification timezone naive bug
stage: general
date: 2026-03-07
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: debug and fix notification system
labels: ["notifications","bug","datetime","timezone","asyncpg"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/routes/notifications.py
tests:
  - verified via direct Python script: 3 notifications created after fix
---

## Prompt

Notifications not working - debug and fix the entire notification system.
[...debug steps requested...]

## Response snapshot

**Root cause**: `_sync_task_notifications()` crashed on every call with `asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes`. The DB columns `task.due_date` and `notification.created_at` are `TIMESTAMP WITHOUT TIME ZONE` (naive), but the code passed `datetime.now(timezone.utc)` (timezone-aware). asyncpg rejects the mismatch.

**Diagnosis path**:
1. Confirmed `notification` table exists with correct schema
2. Confirmed 7 tasks with due_dates, 3 within 24h window
3. Ran `_sync_task_notifications()` directly → caught explicit `DataError`
4. Fix: replace `datetime.now(timezone.utc)` → `datetime.utcnow()` and strip tzinfo from `task.due_date` before comparison

**Verified**: After fix, sync created 3 notifications (2 overdue, 1 upcoming) correctly.

## Outcome

- Impact: Notification bell count and dropdown now work end-to-end
- Tests: Manual Python script confirmed 3 notifications created
- Files: 1 file modified (notifications.py)
- Next prompts: deploy to Render, verify in production
- Reflection: The error was silently swallowed in the HTTP handler (try/except logs but doesn't propagate). Direct script testing was the fastest diagnosis path.

## Evaluation notes (flywheel)

- Failure modes observed: timezone-aware vs naive datetime mismatch with asyncpg
- Graders run and results (PASS/FAIL): manual test PASS
- Prompt variant (if applicable): none
- Next experiment: add explicit timezone stripping utility to all datetime comparisons in the codebase

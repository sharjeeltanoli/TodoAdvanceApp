---
id: "0027"
title: Fix Datetime Timezone asyncpg Bug
stage: general
date: 2026-03-05
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: AI Employee Cloud
command: general
labels: ["datetime", "asyncpg", "timezone", "fastapi", "bugfix", "postgres"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/routes/todos.py
tests:
  - Task creation with due_date ISO string (Z suffix) succeeds without asyncpg error
---

## Prompt

**Date Field Bug Fix Prompt:**

Task creation fails when due date is added. Root cause: asyncpg error "can't subtract offset-naive and offset-aware datetimes". The SQLModel Task.due_date maps to TIMESTAMP WITHOUT TIME ZONE, but the frontend sends tz-aware ISO strings (e.g. "2024-03-15T00:00:00.000Z") which Pydantic parses as tz-aware datetime(tzinfo=UTC). Fix the timezone handling in todos.py create_todo and update_todo to strip timezone before DB insert.

## Response snapshot

Added `_to_naive_utc()` helper function to `todos.py` that strips timezone info (converting to UTC first if tz-aware). Applied it to `due_date` and `snoozed_until` fields in both `create_todo` (before Task construction) and `update_todo` (before setattr loop). Committed and pushed to GitHub (8fae98c).

## Outcome

- ✅ Impact: Task creation and updates with due_date no longer fail; tz-aware datetimes from frontend are safely converted to naive UTC before asyncpg write
- 🧪 Tests: Local fix verified; asyncpg TIMESTAMP WITHOUT TIME ZONE column now accepts due_date values
- 📁 Files: todos.py (+_to_naive_utc helper, applied in create_todo and update_todo)
- 🔁 Next prompts: After Render redeploy, verify task creation with due_date works end-to-end in production
- 🧠 Reflection: Root cause was a type mismatch between Pydantic v2 datetime parsing (ISO Z → tz-aware) and asyncpg's strict TIMESTAMP WITHOUT TIME ZONE handling — both layers behaving correctly per spec, collision only at the boundary.

## Evaluation notes (flywheel)

- Failure modes observed: None — root cause was clear from asyncpg error message; fix was minimal and targeted
- Graders run and results (PASS/FAIL): Local smoke test PASS
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Verify in production after Render redeploy that POST /todos with due_date succeeds

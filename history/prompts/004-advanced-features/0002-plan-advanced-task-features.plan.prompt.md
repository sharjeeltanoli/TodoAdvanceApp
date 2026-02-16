---
id: "0002"
title: "Plan Advanced Task Features"
stage: plan
date: 2026-02-16
surface: agent
model: claude-opus-4-6
feature: 004-advanced-features
branch: 004-advanced-features
user: developer
command: /sp.plan
labels: ["architecture", "plan", "database", "api", "frontend", "recurring", "reminders"]
links:
  spec: specs/004-advanced-features/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/004-advanced-features/plan.md
  - specs/004-advanced-features/research.md
  - specs/004-advanced-features/data-model.md
  - specs/004-advanced-features/quickstart.md
  - specs/004-advanced-features/contracts/api.yaml
tests:
  - none
---

## Prompt

Create architectural plan for Phase 5A advanced features based on specs/004-advanced-features/spec.md

PLAN MUST INCLUDE:
1. Database schema changes (add columns: priority, tags, due_date, recurrence_pattern to tasks table)
2. New table design for task_recurrence metadata
3. API endpoint extensions (query params for search/filter/sort)
4. Frontend UI components (priority selector, tag input, date picker, filters, search bar)
5. Recurring task logic (cron job or scheduled service)
6. Reminder system (browser notifications API)
7. Migration strategy (Alembic migrations for new columns)
8. Backward compatibility (existing tasks get default values)
9. Performance considerations (indexes on priority, due_date, tags)
10. User experience flow (where new features appear in UI)

Reference constitution and existing Phase 2/3 architecture.

Create plan in specs/004-advanced-features/plan.md

## Response snapshot

Created comprehensive implementation plan with 6 phases (A-F) and 5 supporting artifacts:

**Architecture decisions (5)**:
- D1: Tags as JSONB array (not separate table) — GIN index for containment queries
- D2: Priority as TEXT+CHECK (not native PG enum) — easier migration
- D3: Native HTML date input (no external library) — zero bundle impact
- D4: APScheduler for recurring tasks (not Kafka/Celery) — Phase 5B deferral
- D5: Client-side polling for reminders (not WebSocket) — 60s interval, minute precision

**Implementation phases**:
- Phase A: Database migration (6 new columns, 3 new indexes)
- Phase B: API extensions (search/filter/sort params, tags endpoint, snooze endpoint)
- Phase C: Frontend UI (6 new components, 3 modified components)
- Phase D: Recurring tasks (APScheduler, 5-min interval)
- Phase E: Reminders (Notification API, polling, snooze)
- Phase F: MCP tools update (extend 3 tools, add new fields)

**Constitution check**: All principles PASS except IV (Event-Driven) with justified WAIVER — Kafka deferred to Phase 5B per spec.

## Outcome

- ✅ Impact: Complete architectural plan ready for task generation
- 🧪 Tests: No tests — planning artifact only
- 📁 Files: 5 files created (plan.md, research.md, data-model.md, quickstart.md, contracts/api.yaml)
- 🔁 Next prompts: `/sp.tasks` to generate implementation tasks
- 🧠 Reflection: Plan leverages existing codebase patterns well. Key risk is migration backward compat — mitigated by defaults on all new columns.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Constitution check PASS (with one justified waiver)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

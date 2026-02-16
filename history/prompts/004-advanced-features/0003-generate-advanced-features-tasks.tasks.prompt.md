---
id: "0003"
title: "Generate Advanced Features Tasks"
stage: tasks
date: 2026-02-16
surface: agent
model: claude-opus-4-6
feature: 004-advanced-features
branch: 004-advanced-features
user: developer
command: /sp.tasks
labels: ["tasks", "breakdown", "implementation", "priority-ordered"]
links:
  spec: specs/004-advanced-features/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/004-advanced-features/tasks.md
tests:
  - none
---

## Prompt

Break down Phase 5A plan into implementable tasks.

TASK STRUCTURE:
Phase A: Database Migrations (tasks for Alembic migration, model updates)
Phase B: API Extensions (tasks for query params, new endpoints, validation)
Phase C: Frontend UI (tasks for each component: priority selector, tag input, date picker, filters, search)
Phase D: Recurring Tasks (tasks for APScheduler setup, recurrence logic)
Phase E: Reminders (tasks for notification API, polling service)
Phase F: MCP Tools (tasks to extend add_task, update_task tools with new fields)

Group by priority:
- P1 tasks first (priorities, tags, search, filter)
- P2 tasks next (due dates, reminders)
- P3 tasks last (recurring, snooze)

Include acceptance criteria for each task.

Create tasks in specs/004-advanced-features/tasks.md

## Response snapshot

Generated 57 tasks across 13 phases organized by user story:

- **Phase 1 (Setup)**: 2 tasks — install date-fns and apscheduler
- **Phase 2 (Foundation)**: 5 tasks — Alembic migration, model updates, schema validation
- **Phases 3-6 (P1)**: 20 tasks — Priority (5), Tags (6), Due Dates (5), Search (4)
- **Phases 7-9 (P2)**: 10 tasks — Filter (4), Sort (4), Descriptions (2)
- **Phases 10-11 (P3)**: 12 tasks — Recurring (6), Reminders (6)
- **Phase 12 (MCP)**: 5 tasks — extend tools with new fields
- **Phase 13 (Polish)**: 3 tasks — backward compat, integration, quickstart validation

12 tasks marked [P] for parallel execution. MVP scope: Phase 2 + US1 = 10 tasks.

## Outcome

- ✅ Impact: Complete task breakdown ready for implementation
- 🧪 Tests: Not requested — manual verification via acceptance criteria per task
- 📁 Files: 1 file created (tasks.md)
- 🔁 Next prompts: `/sp.implement` to begin task execution or `/sp.analyze` for cross-artifact consistency check
- 🧠 Reflection: Tasks organized by user story enabling independent implementation. Each story has clear checkpoint. Backend route tasks modify same file sequentially — noted in caveats.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Format validation PASS (all tasks have checkbox, ID, story label, file path)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

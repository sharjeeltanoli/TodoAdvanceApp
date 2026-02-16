---
id: "0005"
title: "Remediate HIGH Consistency Issues"
stage: misc
date: 2026-02-16
surface: agent
model: claude-opus-4-6
feature: 004-advanced-features
branch: 004-advanced-features
user: developer
command: /sp.analyze (remediation follow-up)
labels: ["remediation", "consistency", "data-model", "reminders", "snooze"]
links:
  spec: specs/004-advanced-features/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/004-advanced-features/plan.md
  - specs/004-advanced-features/data-model.md
  - specs/004-advanced-features/tasks.md
  - specs/004-advanced-features/contracts/api.yaml
tests:
  - none
---

## Prompt

Yes, apply remediation edits for all 3 HIGH issues (C1, C2, C3):

C1: Fix whatever the first consistency issue is
C2: Add snoozed_until column to tasks table (timestamp nullable)
C3: Add reminder_notified_at column to tasks table (timestamp nullable)

Update:
- specs/004-advanced-features/plan.md (database schema section)
- specs/004-advanced-features/tasks.md (Phase A migration task)

Make sure US9 (reminders/snooze) has proper data model support.

## Response snapshot

Applied all 3 HIGH issue remediations across 4 artifacts:

**C1 (plan.md)**: Fixed D2 heading from "Priority as PostgreSQL Enum" to "Priority as Text with CHECK Constraint (not native PG enum)" — heading now matches body content.

**C2 + C3 (all 4 files)**: Added `snoozed_until TIMESTAMPTZ NULL` and `reminder_notified_at TIMESTAMPTZ NULL` columns:

- **plan.md**: Added columns to Phase A migration list, updated model field list, rewrote Phase E reminders with proper snooze/dedup logic
- **data-model.md**: Added to Fields table, validation rules, and migration steps (now 10 steps instead of 8)
- **tasks.md**: Updated T003 (migration — now lists 8 columns), T005 (Task model — 8 fields), T006 (schemas — includes new response fields), T044 (reminders endpoint — filters on `reminder_notified_at`), T045 (snooze — sets `snoozed_until`, clears `reminder_notified_at`), T048 (polling — PATCHes `reminder_notified_at` after notification)
- **contracts/api.yaml**: Added `snoozed_until` and `reminder_notified_at` to TaskResponse schema, updated reminders endpoint and snooze endpoint descriptions

## Outcome

- ✅ Impact: All 3 HIGH consistency issues resolved — reminder subsystem now has proper state tracking for snooze and deduplication
- 🧪 Tests: N/A — documentation edits only
- 📁 Files: 4 files modified (plan.md, data-model.md, tasks.md, api.yaml)
- 🔁 Next prompts: `/sp.implement` to begin task execution
- 🧠 Reflection: The reminder subsystem (US9) was the weakest part of the original design. Adding two state columns (snoozed_until, reminder_notified_at) creates a clean state machine: notify → mark notified → snooze clears mark → re-notify after snooze.

## Evaluation notes (flywheel)

- Failure modes observed: None — edits applied cleanly
- Graders run and results (PASS/FAIL): All 3 HIGH issues resolved PASS, cross-artifact consistency PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

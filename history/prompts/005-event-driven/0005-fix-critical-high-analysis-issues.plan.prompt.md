---
id: "0005"
title: "Fix Critical High Analysis Issues"
stage: plan
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: 005-event-driven
branch: 005-event-driven
user: architect
command: remediation
labels: ["fix", "analysis", "consistency", "critical", "high"]
links:
  spec: specs/005-event-driven/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-event-driven/contracts/api.yaml
  - specs/005-event-driven/contracts/events.yaml
  - specs/005-event-driven/spec.md
  - specs/005-event-driven/plan.md
  - specs/005-event-driven/tasks.md
tests:
  - none (artifact remediation)
---

## Prompt

Fix all CRITICAL and HIGH issues before implementation:

U-001 (CRITICAL): Add SSE event data schema to contracts/api.yaml
I-001 (HIGH): Resolve task.deleted event data in events.yaml
G-001 (HIGH): Add retry logic for at-least-once delivery
C-001 (HIGH): Add SSE connection registry to plan.md Complexity Tracking
U-002 (HIGH): Add mTLS validation task to Phase 8
U-003 (HIGH): Add consumer group verification to deployment validation
A-001 (HIGH): Clarify reminder dedup window in spec
I-002 (HIGH): Fix topic subscriber listing in plan.md

## Response snapshot

Applied all 8 fixes across 5 files: (1) Added SSETaskUpdate, TaskEventPayload, ReminderPayload, TaskSnapshot schemas to api.yaml with SSE endpoint auth/examples. (2) Fixed events.yaml subscriber list (removed sse-gateway from task-events). (3) Clarified FR-008 dedup to 5-minute window in spec.md. (4) Fixed plan.md: subscriber table, task:null for deletes, retry logic description, 5-min dedup TTL, Complexity Tracking table with SSE justification. (5) Updated tasks.md: T016 now includes retry logic + delete null contract, added T065 (mTLS), T066 (consumer groups), T067 (graceful degradation), updated totals to 67 tasks.

## Outcome

- ✅ Impact: All 8 CRITICAL/HIGH issues resolved; 0 CRITICAL, 0 HIGH remaining
- 🧪 Tests: 3 new validation tasks added (T065-T067) covering mTLS, consumer groups, graceful degradation
- 📁 Files: 5 files modified (api.yaml, events.yaml, spec.md, plan.md, tasks.md)
- 🔁 Next prompts: /sp.implement to begin task execution
- 🧠 Reflection: Dedup window changed from 1h to 5min aligns better with 5-min cron cycle — prevents missing reminders

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): All 8 issues verified resolved
- Prompt variant (if applicable): direct remediation from analysis findings
- Next experiment (smallest change to try): run /sp.analyze again to confirm 0 critical/high

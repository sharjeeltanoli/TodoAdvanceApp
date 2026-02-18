---
id: "0003"
title: "Event-Driven Task Breakdown"
stage: tasks
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: 005-event-driven
branch: 005-event-driven
user: architect
command: /sp.tasks
labels: ["tasks", "event-driven", "dapr", "kafka", "microservices"]
links:
  spec: specs/005-event-driven/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-event-driven/tasks.md
tests:
  - none (task generation phase)
---

## Prompt

Break down Phase 5B Event-Driven plan into implementable tasks.

TASK GROUPS:
1. Setup (Redpanda + Dapr installation on Minikube)
2. Dapr Components (Pub/Sub, State, Cron, Secrets configs)
3. Event Publishing (modify backend CRUD to publish events)
4. Notification Service (new microservice - consumes reminders topic)
5. Recurring Task Service (new microservice - consumes task-events)
6. WebSocket Service (real-time sync via task-updates topic)
7. Dapr Sidecar (inject into all K8s deployments)
8. Helm Chart Updates (add new services to chart)
9. Audit Trail (event logging)
10. Testing & Validation

Reference:
- specs/005-event-driven/plan.md
- .claude/skills/dapr-configuration/SKILL.md

Create tasks in specs/005-event-driven/tasks.md

## Response snapshot

Generated 64 tasks across 8 phases organized by user story priority. Phase 1 (Setup): 4 tasks for Redpanda/Redis/Dapr installation. Phase 2 (Foundational): 23 tasks covering Dapr components, DB migration, event publishing framework, backend integration, Helm infrastructure. Phase 3 (US1 Real-Time Sync): 8 tasks for SSE gateway service + frontend SSE client. Phase 4 (US2 Reminders): 13 tasks for cron handler + notification microservice + frontend UI. Phase 5 (US3 Recurring): 2 tasks enhancing event handler. Phase 6 (US4 Audit Trail): 4 tasks for history endpoint + frontend. Phase 7 (MCP): 2 tasks. Phase 8 (Polish): 8 validation tasks. 22 tasks parallelizable. Design decision: recurring task handling stays in backend (event-driven via task.completed subscriber) rather than separate microservice.

## Outcome

- ✅ Impact: 64 implementable tasks with exact file paths, dependency graph, parallel execution opportunities
- 🧪 Tests: Validation tasks in Phase 8 (T059-T064) cover all user stories end-to-end
- 📁 Files: 1 artifact (specs/005-event-driven/tasks.md)
- 🔁 Next prompts: /sp.implement to begin execution, or /sp.analyze for cross-artifact consistency check
- 🧠 Reflection: Kept recurring task as backend event handler (T049) not separate service — avoids duplicating DB access. US1+US2 can run in parallel after foundational phase.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Format validation PASS (all tasks have checkbox + ID + file paths)
- Prompt variant (if applicable): standard /sp.tasks with 10-group user input
- Next experiment (smallest change to try): verify Dapr component YAML correctness against actual Dapr v1.14 schema

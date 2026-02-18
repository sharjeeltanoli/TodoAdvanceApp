---
id: "0007"
title: Phase 3 and Phase 4 User Story Implementation
stage: green
date: 2026-02-18
surface: agent
model: claude-opus-4-6
feature: 005-event-driven
branch: 005-event-driven
user: architect
command: /sp.implement
labels: ["sse-gateway", "notifications", "real-time", "cron", "frontend"]
links:
  spec: specs/005-event-driven/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/services/sse_gateway/__init__.py
  - backend/services/sse_gateway/requirements.txt
  - backend/services/sse_gateway/connections.py
  - backend/services/sse_gateway/main.py
  - backend/services/sse_gateway/Dockerfile
  - backend/services/notification/__init__.py
  - backend/services/notification/requirements.txt
  - backend/services/notification/models.py
  - backend/services/notification/handlers.py
  - backend/services/notification/main.py
  - backend/services/notification/Dockerfile
  - backend/app/events/handlers.py
  - backend/app/routes/notifications.py
  - backend/app/main.py
  - frontend/src/lib/sse.ts
  - frontend/src/components/tasks/task-list.tsx
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/app/dashboard/dashboard-client.tsx
  - frontend/src/app/dashboard/layout.tsx
  - frontend/src/components/notifications/notification-bell.tsx
  - frontend/src/components/notifications/notification-list.tsx
  - specs/005-event-driven/tasks.md
tests:
  - none (validation in Phase 8)
---

## Prompt

continue with Phase 3 and Phase 4 implementation

## Response snapshot

Implemented all 21 tasks across Phase 3 (US1 - Real-Time Sync) and Phase 4 (US2 - Notifications):

**Phase 3 — SSE Gateway Service (T028-T032)**:
- `connections.py`: ConnectionManager with per-user asyncio.Queue sets for fan-out
- `main.py`: FastAPI app with `/dapr/subscribe`, `/events/task-updates` handler, `/stream/tasks` SSE endpoint with Bearer auth validation and 30s heartbeat
- Dockerfile on port 8003, requirements.txt

**Phase 3 — Frontend SSE (T033-T035)**:
- `sse.ts`: createTaskSSEConnection() with exponential backoff reconnect (1s-30s, 10 retries)
- `task-list.tsx`: SSE connection on mount, refetch tasks on events, live status indicator (green dot)
- `dashboard-client.tsx`: Client wrapper that resolves auth token and passes to TaskList
- `page.tsx`: Uses DashboardClient for SSE-enabled task list

**Phase 4 — Cron Handler (T036-T037)**:
- `/cron-overdue-check` endpoint in handlers.py: queries upcoming (1h) and overdue tasks, dedup via Dapr state store, publishes to reminders topic

**Phase 4 — Notification Service (T038-T043)**:
- Full FastAPI microservice at backend/services/notification/
- Subscribes to reminders topic, creates Notification records with idempotency
- REST endpoints: list (cursor pagination), mark read, mark all read, unread count
- Dockerfile on port 8002

**Phase 4 — Backend Proxy (T044-T045)**:
- `notifications.py`: Proxy routes forwarding to notification-svc via Dapr service invocation
- Registered in main.py

**Phase 4 — Frontend UI (T046-T048)**:
- `notification-bell.tsx`: Bell icon with unread count badge, 30s polling
- `notification-list.tsx`: Dropdown panel with notification list, mark read, mark all read
- Integrated into dashboard layout header

## Outcome

- ✅ Impact: Complete US1 (real-time sync) and US2 (notifications) — 21/21 tasks completed (T028-T048, T049 also done)
- 🧪 Tests: None (validation in Phase 8)
- 📁 Files: 22 files created/modified
- 🔁 Next prompts: Phase 5 (T050), Phase 6 (T051-T054), Phase 7 (T055-T056), Phase 8 (validation)
- 🧠 Reflection: Both user stories implemented end-to-end including backend services, Dapr integration, and frontend UI

## Evaluation notes (flywheel)

- Failure modes observed: None — straightforward implementation following established patterns
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Deploy to Minikube and validate SSE connection + notification flow end-to-end

---
id: "0002"
title: "Event-Driven Architecture Plan"
stage: plan
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: 005-event-driven
branch: 005-event-driven
user: architect
command: /sp.plan
labels: ["event-driven", "dapr", "kafka", "redpanda", "architecture"]
links:
  spec: specs/005-event-driven/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-event-driven/plan.md
  - specs/005-event-driven/research.md
  - specs/005-event-driven/data-model.md
  - specs/005-event-driven/quickstart.md
  - specs/005-event-driven/contracts/api.yaml
  - specs/005-event-driven/contracts/events.yaml
tests:
  - none (planning phase)
---

## Prompt

Create architectural plan for Phase 5B Event-Driven Architecture based on specs/005-event-driven/spec.md

PLAN MUST INCLUDE:
1. Kafka/Redpanda setup (local Minikube + cloud)
2. Dapr components design (using .claude/skills/dapr-configuration/)
3. 3 Kafka topics architecture (task-events, reminders, task-updates)
4. 2 new microservices (Notification + Recurring Task Service)
5. Event publishing in existing backend (after each CRUD operation)
6. WebSocket service for real-time frontend sync
7. Dapr sidecar injection in all K8s deployments
8. Cron binding for overdue task checks
9. State store for conversation cache
10. Service invocation patterns
11. Local development workflow (Redpanda on Minikube)
12. Production setup (Redpanda Cloud)

Reference:
- .claude/skills/dapr-configuration/SKILL.md
- .claude/skills/observability-monitoring/SKILL.md
- Existing architecture from Phase 3/4

Create plan in specs/005-event-driven/plan.md

## Response snapshot

Generated comprehensive architectural plan covering all 12 requested areas. Key decisions: Redpanda as Kafka-compatible broker (lighter than Kafka for local dev), Dapr pub/sub abstraction (constitution mandated), SSE over WebSocket for real-time sync (unidirectional, existing pattern), 2 new services (Notification Service + SSE Gateway) instead of 3 (recurring task handling stays in backend). Created 6 artifacts: plan.md, research.md, data-model.md, quickstart.md, contracts/api.yaml, contracts/events.yaml.

## Outcome

- ✅ Impact: Complete architectural plan for event-driven system with 5 service deployments, 3 Kafka topics, Dapr runtime integration
- 🧪 Tests: N/A (planning phase — tests defined in tasks.md)
- 📁 Files: 6 artifacts created in specs/005-event-driven/
- 🔁 Next prompts: /sp.tasks to generate implementation tasks, /sp.adr for Dapr/Redpanda decision
- 🧠 Reflection: Design favors SSE over WebSocket (simpler, unidirectional) and keeps recurring task logic in backend (avoids unnecessary service proliferation)

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Constitution check PASS (all 6 principles + security)
- Prompt variant (if applicable): standard /sp.plan with explicit 12-point requirements
- Next experiment (smallest change to try): validate Redpanda Helm chart works on Minikube with available resources

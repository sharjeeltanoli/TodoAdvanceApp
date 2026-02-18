---
id: "0001"
title: "Event-Driven Todo Specification"
stage: spec
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: 005-event-driven
branch: 005-event-driven
user: architect
command: /sp.specify
labels: ["event-driven", "kafka", "dapr", "pubsub", "microservices"]
links:
  spec: specs/005-event-driven/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-event-driven/spec.md
  - specs/005-event-driven/checklists/requirements.md
tests:
  - null
---

## Prompt

Create Phase 5B specification for Event-Driven Architecture with Kafka and Dapr.

FEATURE: Event-Driven Todo System with Kafka messaging and Dapr runtime

REQUIREMENTS:
1. Kafka Integration (3 topics):
   - task-events: All CRUD operations publish events
   - reminders: Due date notification triggers
   - task-updates: Real-time client sync

2. Dapr Components:
   - Pub/Sub: Kafka abstraction (publish/subscribe)
   - State Management: Conversation cache
   - Cron Binding: Check overdue tasks every 5 mins
   - Secrets: Secure credential management
   - Service Invocation: Inter-service calls

3. New Microservices:
   - Notification Service: Consumes reminders topic
   - Recurring Task Service: Consumes task-events topic

4. Local Deployment:
   - Redpanda (Kafka-compatible) on Minikube
   - Dapr installed on Minikube
   - All services with Dapr sidecars

TECH STACK:
- Kafka: Redpanda (local) / Redpanda Cloud (production)
- Dapr: v1.14+
- Python: aiokafka for direct Kafka (fallback)
- Use .claude/skills/dapr-configuration/ skill
- Use .claude/skills/observability-monitoring/ skill

Create specification in specs/005-event-driven/ directory

## Response snapshot

Created feature specification for Event-Driven Todo System (Phase 5B) with 4 user stories (Real-Time Sync P1, Reminders P1, Recurring Tasks P2, Audit Trail P3), 20 functional requirements across 6 categories (event publishing, reminders, real-time sync, recurring tasks, consumer reliability, service communication), 4 key entities, 6 edge cases, 7 assumptions, and 8 measurable success criteria. All quality checklist items pass — no clarifications needed.

## Outcome

- Impact: Created comprehensive event-driven architecture spec covering Kafka topics, Dapr components, and new microservices
- Tests: No tests yet — spec phase
- Files: spec.md, checklists/requirements.md
- Next prompts: /sp.clarify or /sp.plan
- Reflection: User requirements were detailed enough to avoid any NEEDS CLARIFICATION markers

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Quality checklist PASS (all items)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null

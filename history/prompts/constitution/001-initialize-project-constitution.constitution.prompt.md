---
id: 001
title: Initialize Project Constitution
stage: constitution
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: user
command: /sp.constitution
labels: ["constitution", "project-setup", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
---

## Prompt

Update the constitution file at .specify/memory/constitution.md. Replace all template placeholders with actual hackathon requirements:

PROJECT: Hackathon Todo - Evolution from Web App to Cloud-Native AI System

TECH STACK:
- Frontend: Next.js 16+ (App Router), TypeScript, Tailwind CSS, OpenAI ChatKit
- Backend: Python 3.13+, FastAPI, SQLModel
- Database: Neon Serverless PostgreSQL
- Auth: Better Auth with JWT
- AI: OpenAI Agents SDK, Official MCP SDK
- Infrastructure: Docker, Kubernetes, Helm, Kafka, Dapr

PRINCIPLES:
1. Spec-Driven Development: No manual coding, all via Claude Code
2. Monorepo: frontend/ and backend/ in single repo
3. Stateless Services: All state in database
4. Event-Driven: Kafka for async operations
5. User Isolation: All queries filter by user_id
6. MCP Protocol: AI-to-app communication

SECURITY:
- JWT authentication required on all API endpoints
- Authorization: Bearer <token> header
- User data filtered by authenticated user_id
- Environment variables for secrets
- CORS properly configured

PHASES:
- Phase 2: Full-stack web app (Next.js + FastAPI + Neon)
- Phase 3: AI chatbot with MCP tools
- Phase 4: Local Kubernetes deployment
- Phase 5: Cloud deployment with Kafka + Dapr

Update the file completely and confirm when done.

## Response snapshot

Replaced all template placeholders in `.specify/memory/constitution.md` with concrete project values. Created version 1.0.0 with 6 core principles (Spec-Driven Development, Monorepo Structure, Stateless Services, Event-Driven Architecture, User Isolation, MCP Protocol), Security Requirements section, Development Phases section (Phases 2-5), and Governance rules. All principles use declarative MUST/MUST NOT language. Sync Impact Report embedded as HTML comment. No template updates required (all are generic).

## Outcome

- Impact: Constitution initialized from template to v1.0.0 with full project-specific principles and constraints
- Tests: N/A (documentation artifact)
- Files: .specify/memory/constitution.md
- Next prompts: /sp.specify for first feature, /sp.plan for architecture
- Reflection: Clean first-time constitution setup; all 6 user-provided principles mapped directly to constitution sections

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual validation PASS — no unresolved placeholders, all principles declarative and testable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

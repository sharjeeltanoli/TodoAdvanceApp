---
id: 0003
title: Research FastAPI SQLModel Neon Architecture
stage: general
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: user
command: research
labels: ["fastapi", "sqlmodel", "neon", "postgresql", "jwt", "better-auth", "alembic", "architecture"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/general/0003-research-fastapi-sqlmodel-neon-architecture.general.prompt.md
tests:
  - none
---

## Prompt

Research FastAPI with SQLModel and Neon Serverless PostgreSQL for a todo CRUD application. I need to understand:
1. FastAPI project structure best practices (routers, models, dependencies, services)
2. SQLModel usage patterns - defining models that work as both Pydantic models and SQLAlchemy models
3. How to connect SQLModel to Neon Serverless PostgreSQL (connection string, async support)
4. JWT token verification in FastAPI - how to validate tokens issued by an external auth provider (Better Auth)
5. Dependency injection pattern for extracting user_id from JWT in every request
6. Database migration strategy with SQLModel (Alembic integration)

Return concise findings focused on architecture decisions.

## Response snapshot

Comprehensive research findings delivered covering all 6 topics. Key decisions: domain-based project structure, SQLModel multiple-model inheritance pattern (Base/Table/Create/Public), async engine with asyncpg for Neon, Better Auth bearer token verification via /api/auth/get-session or direct session_token lookup, FastAPI dependency chain for JWT extraction, and Alembic async template with SQLModel.metadata.

## Outcome

- Impact: Research complete for all 6 architecture topics needed for Phase 2 backend
- Tests: N/A - research only
- Files: PHR created
- Next prompts: Create spec.md and plan.md for the todo CRUD backend feature
- Reflection: Better Auth uses session tokens (not standard JWTs) by default; the bearer plugin or direct DB session lookup are the two verification strategies for a Python backend

## Evaluation notes (flywheel)

- Failure modes observed: Better Auth documentation for Python backend verification is sparse; most examples are JS/TS
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

<!--
  Sync Impact Report
  ===================
  Version change: 0.0.0 (template) -> 1.0.0

  Modified principles:
    - [PRINCIPLE_1_NAME] -> I. Spec-Driven Development
    - [PRINCIPLE_2_NAME] -> II. Monorepo Structure
    - [PRINCIPLE_3_NAME] -> III. Stateless Services
    - [PRINCIPLE_4_NAME] -> IV. Event-Driven Architecture
    - [PRINCIPLE_5_NAME] -> V. User Isolation
    - [PRINCIPLE_6_NAME] -> VI. MCP Protocol

  Added sections:
    - Security Requirements (Section 2)
    - Development Phases (Section 3)

  Removed sections:
    - None (all template sections filled)

  Templates requiring updates:
    - .specify/templates/plan-template.md — No updates needed (generic)
    - .specify/templates/spec-template.md — No updates needed (generic)
    - .specify/templates/tasks-template.md — No updates needed (generic)

  Deferred TODOs:
    - RATIFICATION_DATE set to today (first adoption)
-->

# Hackathon Todo Constitution

## Core Principles

### I. Spec-Driven Development

All features and changes MUST be driven through the SDD workflow.
No manual coding outside of Claude Code-driven implementation is permitted.
Every feature MUST have a specification (`spec.md`), implementation
plan (`plan.md`), and task list (`tasks.md`) before code is written.
Changes without corresponding spec artifacts MUST be rejected in review.

### II. Monorepo Structure

The project MUST use a single repository with `frontend/` and `backend/`
top-level directories. All shared configuration (Docker, Kubernetes,
Helm charts, CI/CD) lives at the repository root. Cross-cutting concerns
(types, contracts, environment configs) MUST be co-located to enable
atomic commits across the stack.

### III. Stateless Services

All application state MUST be persisted in the database (Neon Serverless
PostgreSQL). Backend services MUST NOT rely on in-memory state between
requests. Session data, user preferences, and transient state MUST be
stored externally. This enables horizontal scaling and zero-downtime
deployments in Kubernetes.

### IV. Event-Driven Architecture

Asynchronous operations MUST use Kafka for inter-service communication.
Synchronous request-response is permitted only for direct user-facing
API calls. Long-running operations (AI processing, batch updates) MUST
be published as events and processed asynchronously. Dapr MUST be used
as the eventing abstraction layer in Phase 5.

### V. User Isolation

Every database query MUST filter by the authenticated `user_id`. No
endpoint may return or modify data belonging to another user. Multi-tenant
data access MUST be enforced at the service layer, not solely at the API
layer. Missing `user_id` filters MUST be treated as a security defect.

### VI. MCP Protocol

AI-to-application communication MUST use the Model Context Protocol (MCP).
MCP tools MUST be the sole interface for AI agents to read and mutate
application state. Direct database access from AI agents is prohibited.
All MCP tool invocations MUST be authenticated and authorized against the
requesting user's permissions.

## Security Requirements

- JWT authentication MUST be required on all API endpoints. Unauthenticated
  requests MUST receive a 401 response.
- The `Authorization: Bearer <token>` header MUST be the sole authentication
  mechanism for API requests.
- All user-scoped data MUST be filtered by the authenticated `user_id`
  extracted from the verified JWT.
- Secrets, tokens, and credentials MUST be stored in environment variables
  or a secrets manager. Hardcoded secrets MUST be rejected in review.
- CORS MUST be configured to allow only the frontend origin in production.
  Wildcard (`*`) origins are permitted only in local development.
- Dependencies MUST be pinned to exact versions. Security advisories MUST
  be reviewed before upgrading.

## Development Phases

The project evolves through defined phases. Each phase builds on the
previous and MUST NOT break functionality delivered in earlier phases.

- **Phase 2 — Full-Stack Web App**: Next.js 16+ (App Router) frontend
  with TypeScript and Tailwind CSS. FastAPI backend with SQLModel ORM.
  Neon Serverless PostgreSQL database. Better Auth with JWT for
  authentication. This is the foundational deliverable.
- **Phase 3 — AI Chatbot with MCP Tools**: OpenAI Agents SDK integration.
  OpenAI ChatKit for the chat UI. Official MCP SDK for tool definitions.
  AI agents interact with the app exclusively through MCP tools.
- **Phase 4 — Local Kubernetes Deployment**: Docker containerization of
  frontend and backend. Helm charts for Kubernetes deployment. Local
  cluster validation (e.g., kind, minikube, Docker Desktop).
- **Phase 5 — Cloud Deployment**: Kafka for event-driven async operations.
  Dapr sidecar for service invocation, pub/sub, and state management.
  Production-grade observability and scaling configuration.

## Governance

This constitution is the authoritative source for project principles and
constraints. All specifications, plans, and code reviews MUST verify
compliance with these principles.

- **Amendments**: Any change to this constitution MUST be documented with
  rationale, approved by the project lead, and accompanied by a migration
  plan for affected artifacts.
- **Versioning**: The constitution follows semantic versioning. MAJOR for
  principle removals or redefinitions, MINOR for new principles or
  material expansions, PATCH for clarifications and wording fixes.
- **Compliance**: Every PR MUST be checked against applicable principles.
  Violations MUST be resolved before merge or explicitly justified in a
  Complexity Tracking table.

**Version**: 1.0.0 | **Ratified**: 2026-02-08 | **Last Amended**: 2026-02-08

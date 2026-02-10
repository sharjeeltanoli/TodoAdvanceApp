# Phase 0: Research — Todo CRUD Application

**Feature**: 001-todo-crud
**Date**: 2026-02-08
**Status**: Complete

## R-001: Better Auth Integration with FastAPI

**Decision**: Better Auth runs in Next.js as the auth server. FastAPI acts as a resource server that verifies tokens via Better Auth's Bearer plugin.

**Rationale**: Better Auth manages user registration, login, sessions, and token issuance natively within the Next.js App Router. The JWT plugin provides short-lived JWTs and a JWKS endpoint. FastAPI verifies Bearer tokens either by calling Better Auth's `/api/auth/get-session` endpoint or by direct database session lookup (both share the same Neon database). This avoids implementing custom auth logic in FastAPI while satisfying the constitution's `Authorization: Bearer <token>` requirement.

**Alternatives considered**:
- Custom JWT implementation in FastAPI: Rejected — duplicates auth logic, violates single-source-of-truth.
- Session cookie passthrough: Rejected — constitution mandates Bearer token auth for API requests.
- Separate auth service (Keycloak, Auth0): Rejected — over-engineered for Phase 2; Better Auth is specified in constitution.

## R-002: Next.js 16 App Router Architecture

**Decision**: Hybrid communication pattern — Server Components fetch FastAPI directly for reads; client-side mutations go through Server Actions or Route Handlers as BFF proxy.

**Rationale**: Next.js 16 renamed `middleware.ts` to `proxy.ts` (runs on Node.js, not Edge). Server Components can call FastAPI directly with the backend URL (never exposed to client). Client Components use Server Actions for mutations with automatic cache revalidation. This minimizes latency while keeping the backend URL server-side only.

**Alternatives considered**:
- Full BFF proxy (all traffic through Route Handlers): Rejected — adds unnecessary latency for server-rendered pages.
- Direct client-to-FastAPI calls: Rejected — exposes backend URL to browser, breaks CORS policy intent.

## R-003: SQLModel with Async PostgreSQL

**Decision**: Async SQLModel with `asyncpg` driver connecting to Neon Serverless PostgreSQL. Alembic for migrations.

**Rationale**: SQLModel provides a single model definition for both database schema and Pydantic API schemas. The async engine (`postgresql+asyncpg://`) enables non-blocking I/O matching FastAPI's async nature. Neon handles connection pooling server-side, so modest pool sizes (5-10) suffice.

**Alternatives considered**:
- SQLAlchemy + Pydantic separately: Rejected — duplicates model definitions.
- Prisma (Python client): Rejected — limited Python ecosystem support, better suited for Node.js.
- Sync SQLModel: Rejected — blocks the event loop in FastAPI async handlers.

## R-004: Frontend-Backend Communication Pattern

**Decision**: Three-tier approach for auth defense-in-depth.

**Rationale**:
1. **`proxy.ts`** (formerly middleware): Fast cookie-existence check, redirect unauthenticated users to `/login`. No full JWT validation.
2. **Server Components / Server Actions**: Verify session, extract user identity, pass `Authorization: Bearer <token>` to FastAPI.
3. **FastAPI**: Independently validates Bearer token and filters all queries by `user_id`.

This satisfies CVE-2025-29927 lessons (proxy-only auth is insufficient) and the constitution's User Isolation principle.

**Alternatives considered**:
- Proxy-only protection: Rejected — proven bypassable (CVE-2025-29927).
- Backend-only auth: Rejected — allows unauthenticated UI rendering, poor UX.

## R-005: Database Schema Strategy

**Decision**: Shared Neon database with separate table ownership. Better Auth manages `user`, `session`, `account`, `verification`, and `jwks` tables. FastAPI manages `task` table. Linked by `user_id` foreign key.

**Rationale**: Single database simplifies deployment and enables direct session lookup for performance. Better Auth's Kysely adapter supports PostgreSQL natively. The `user_id` in the `task` table references Better Auth's `user.id`.

**Alternatives considered**:
- Separate databases for auth and app: Rejected — adds operational complexity for a hackathon project; no benefit at this scale.
- FastAPI manages its own user table: Rejected — duplicates user data, violates single-source-of-truth.

## R-006: API URL Design

**Decision**: Use `/api/todos` (not `/api/{user_id}/tasks`) with `user_id` extracted from the JWT Bearer token.

**Rationale**: Putting `user_id` in the URL path is an anti-pattern — it enables IDOR attacks if the authorization check fails. The authenticated `user_id` should come exclusively from the verified JWT token, not from user-supplied URL parameters. This aligns with the constitution's User Isolation principle: "enforced at the service layer, not solely at the API layer."

**Alternatives considered**:
- `/api/{user_id}/tasks` as specified in user input: Rejected — IDOR vulnerability risk; user_id in URL can be manipulated.
- `/api/me/tasks`: Considered acceptable but `/api/todos` is simpler and equally secure since user_id always comes from the token.

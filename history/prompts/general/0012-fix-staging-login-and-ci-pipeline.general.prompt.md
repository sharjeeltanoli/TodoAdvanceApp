---
id: "0012"
title: Fix Staging Login and CI Pipeline
stage: green
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 006-cloud-deployment
branch: main
user: root
command: manual
labels: ["staging","alembic","migrations","ci","better-auth","database-url","publisher","async-session","deploy-workflow","doks"]
links:
  spec: specs/006-cloud-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/alembic/versions/004_add_advanced_fields.py
  - backend/app/events/publisher.py
  - chart/values-staging.yaml
  - .github/workflows/deploy-staging.yml
  - .github/workflows/deploy-production.yml
tests:
  - "alembic current → 005 (head)"
  - "POST /api/auth/sign-up/email → HTTP 200 + session token"
  - "POST /api/auth/sign-in/email → HTTP 200 + redirect to /"
  - "GET /api/todos (Bearer token) → []"
  - "POST /api/todos → task created with all advanced fields"
  - "CI Build and Push Images → success"
  - "CI Deploy to Staging → success (all 6 pods Running)"
---

## Prompt

[Continued from previous session] Fix staging login failure and remaining issues:
1. Alembic migrations 004 and 005 not applied (column task.priority does not exist)
2. DATABASE_URL format wrong for Better Auth (postgresql+asyncpg:// vs postgresql://)
3. Login hanging at "Signing in..."

## Response snapshot

Resolved 7 issues to bring staging to full working state:

**Issue 1 — Alembic migration 004 GIN index**: `data type json has no default operator class for access method "gin"` — fixed by casting `tags::jsonb` in the CREATE INDEX statement. Applied migration 004 successfully.

**Issue 2 — Alembic migration 005 DuplicateTableError**: `task_event`, `notification`, `processed_event` tables already existed (created via SQLModel `create_all`). Stamped migration 005 as applied: `alembic stamp 005`. DB now at `005 (head)`.

**Issue 3 — Pods restarted** to pick up updated DATABASE_URL secret (changed from `postgresql+asyncpg://` to `postgresql://` in previous session).

**Issue 4 — BETTER_AUTH_URL SSL failure**: Backend used httpx to call `https://todo-staging.165-245-153-207.nip.io/api/auth/get-session` — failed with `SSL: CERTIFICATE_VERIFY_FAILED` because letsencrypt-staging cert is not trusted. Fixed by changing `betterAuthUrl` to internal cluster DNS: `http://todo-app-staging-frontend:3000`.

**Issue 5 — ResourceClosedError in publisher**: `asyncio.create_task(publish_task_event(..., db))` shared the request's DB session with a background task. Route handler closed the session; background task tried to commit → `ResourceClosedError: This transaction is closed`. Fixed by creating a fresh `async_session()` inside `publish_task_event` instead of reusing the caller's session.

**Issue 6 — Deploy workflow SHA pinning**: `actions/checkout` and `digitalocean/action-doctl` had invalid pinned SHAs. Removed SHA pinning, switched to version tags (@v4, @v2).

**Issue 7 — Wrong DOKS cluster name**: Deploy workflow used `hackathon-todo` then `todo-app-cluster` — neither matched the actual working cluster `k8s-1-34-1-do-3-nyc1-1771651785370`. Fixed. Also added `DIGITALOCEAN_ACCESS_TOKEN` as GitHub secret.

## Outcome

- ✅ Impact: Full staging deployment working — login, todo CRUD, CI auto-deploy all functional
- 🧪 Tests: sign-up → 200 + session, sign-in → 200 + redirect, GET /todos → [], POST /todos → task with advanced fields, CI → Build success + Deploy success
- 📁 Files: 5 modified
- 🔁 Next: Set up Redpanda Cloud, switch cert-issuer to letsencrypt-prod
- 🧠 Reflection: Background tasks must never share request-scoped DB sessions. Internal cluster DNS avoids staging TLS issues. DOKS cluster name must match exactly.

## Evaluation notes (flywheel)

- Failure modes observed: Session sharing across async boundary; SSL verify in-cluster; wrong cluster name in CI; migration stamp vs apply distinction
- Graders run and results (PASS/FAIL): All 7 manual end-to-end checks PASS
- Prompt variant (if applicable): null
- Next experiment: Run Redpanda Cloud setup and update REDPANDA_* secrets

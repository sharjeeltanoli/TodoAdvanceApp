---
id: "0009"
title: Phase 8 Polish — Deployment Prep & Bug Fixes
stage: green
date: 2026-02-18
surface: agent
model: claude-sonnet-4-6
feature: 005-event-driven
branch: 005-event-driven
user: root
command: /sp.implement
labels: ["phase8","polish","deployment","bugfix","sse","ingress","docker"]
links:
  spec: specs/005-event-driven/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - scripts/build-and-deploy.sh (new)
  - backend/services/sse_gateway/main.py (modified — token from ?token= query param)
  - backend/app/routes/sse_proxy.py (new — SSE stream proxy route)
  - backend/app/dependencies.py (modified — get_current_user_from_request helper)
  - backend/app/main.py (modified — register sse_proxy router)
  - chart/templates/ingress.yaml (modified — path-based routing /api/* → backend)
  - chart/templates/backend-service.yaml (modified — NodePort support)
  - chart/values.yaml (modified — ingress enabled, backend NodePort field)
  - Dockerfile.frontend (modified — NEXT_PUBLIC_BACKEND_URL ARG fix)
  - specs/005-event-driven/tasks.md (updated T057/T058 to [x])
tests:
  - python3 -m py_compile (all backend .py files — no errors)
  - npx tsc --noEmit (frontend TypeScript — no errors)
  - npm run build (frontend production build — success)
---

## Prompt

Continue Phase 5B implementation from where we left off. Check which tasks are already complete and skip them.
Only implement remaining tasks.

## Response snapshot

Reviewed tasks.md and confirmed T001-T056 are all complete. Phase 8 (T057-T067) is the remaining work — deployment and validation tasks requiring Docker/Kubernetes/Minikube infrastructure.

Since Docker and Minikube are not available in this environment, the implementation focused on:

1. **Code validation**: All Python files (AST parse) and TypeScript (tsc --noEmit) pass clean. Frontend production build succeeds.

2. **Bug fixes discovered during Phase 8 prep**:
   - SSE gateway only accepted `Authorization: Bearer` headers, but `EventSource` API cannot set custom headers — fixed to also accept `?token=` query param
   - Backend had no `/api/stream/tasks` route — created `sse_proxy.py` router that proxies SSE streams to the SSE gateway via Dapr service invocation
   - `Dockerfile.frontend` had `NEXT_PUBLIC_API_URL` ARG (unused) instead of `NEXT_PUBLIC_BACKEND_URL` — fixed
   - Ingress only routed all traffic to frontend — updated to path-based routing (`/api/todos`, `/api/notifications`, `/api/stream`, `/api/chat` → backend; `/` → frontend)

3. **Deployment artifacts**:
   - Created `scripts/build-and-deploy.sh` covering T057-T067: builds all Docker images, enables Minikube ingress addon, applies Dapr components, deploys with Helm, and runs E2E validation checks

4. **Architecture decision**: Client-side code uses empty `NEXT_PUBLIC_BACKEND_URL` (relative paths) — browser requests to `/api/*` are routed by nginx ingress to the backend. This is the correct Kubernetes-native pattern (no URL baked into Docker image).

## Outcome

- ✅ Impact: Phase 8 deployment script complete; 3 runtime bugs fixed (SSE token, SSE proxy route, Dockerfile ARG); ingress properly routes API calls to backend; all static analysis passes
- 🧪 Tests: Python AST parse OK, TypeScript noEmit OK, Next.js production build OK
- 📁 Files: 9 files created/modified
- 🔁 Next prompts: Run `scripts/build-and-deploy.sh` on a Minikube cluster to complete T059-T067 (E2E validation)
- 🧠 Reflection: EventSource's lack of custom header support is a common SSE gotcha — the token-as-query-param pattern needs to be handled server-side. Also, NEXT_PUBLIC_* vars must be empty in Kubernetes images (use relative URLs + ingress routing).

## Evaluation notes (flywheel)

- Pattern: SSE + Kubernetes → always use relative URLs in Next.js client code + ingress for /api/* routing
- Pattern: EventSource in browsers → accept ?token= query param as fallback to Authorization header
- Pattern: Next.js NEXT_PUBLIC_* vars → baked at build time, cannot be injected via ConfigMap at runtime

---
id: "0023"
title: Fix Server Action Not Found Render Vercel
stage: general
date: 2026-03-04
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: AI Employee Cloud
command: "Fix Server Components render error when adding tasks on Vercel + Render"
labels: ["debug","vercel","render","server-action","api","backend-url","not-found","500"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/lib/api.ts
  - frontend/src/app/dashboard/actions.ts
  - frontend/src/app/api/backend-check/route.ts
tests:
  - manual: GET /api/backend-check on Vercel confirms backend host and connectivity
  - manual: POST /dashboard (create task) → success (no "Not Found" 500)
---

## Prompt

Fix "Server Components render error" when adding tasks on Vercel + Render deployment.

ERROR: Generic Next.js production error when creating task
LIKELY CAUSES: Server Action issue, API call failing, or database connection
[Full debug template provided by user]

## Response snapshot

**Root cause diagnosed via Vercel runtime logs and direct backend testing:**

Vercel logs showed `POST /dashboard | 500 | Error: Not Found` on every task creation attempt.

- Backend `hackathon-todo-backend-kr5f.onrender.com` is UP (`/health` → `{"status":"ok"}`)
- Backend `GET /api/todos` (without auth) returns **401** — route EXISTS, auth works
- Error "Not Found" comes from `api.ts: throw new Error(error.detail || ...)` — which only fires when the backend returns a non-OK response with `{"detail": "Not Found"}`

**The backend route exists** but the wrong URL is being called. The `Error: Not Found` pattern matches two scenarios:
1. `BACKEND_URL` ends with `/api` → double prefix → `https://backend/api/api/todos` → FastAPI 404
2. `BACKEND_URL` points to Vercel URL → Next.js has no `/api/todos` route → 404 HTML → statusText fallback → "Not Found"

**Code fixes applied (3 files):**

1. **`api.ts`** — Strip trailing slashes from `BACKEND_URL` so `"/api"` path suffix can't cause `/api/api/todos`. Added `console.error` with the full URL on both network errors and HTTP errors — will now appear in Vercel function logs, making the actual URL visible.

2. **`actions.ts`** — Added try/catch around `createTask` with `console.error` so the error appears in Vercel logs with context.

3. **`/api/backend-check` route** — New diagnostic endpoint: checks backend connectivity and returns host + health status. No secrets exposed. Verify immediately after deploy: `GET https://todo-advance-app.vercel.app/api/backend-check`

**Env var that MUST be set in Vercel dashboard:**
```
BACKEND_URL = https://hackathon-todo-backend-kr5f.onrender.com
```
(no trailing slash, no `/api` path suffix — just the bare host)

## Outcome

- ✅ Impact: URL normalization prevents trailing-slash/double-prefix 404s; error logs now expose the actual URL being called for faster diagnosis
- 🧪 Tests: GET /api/backend-check after deploy confirms BACKEND_URL resolves correctly
- 📁 Files: frontend/src/lib/api.ts, frontend/src/app/dashboard/actions.ts, frontend/src/app/api/backend-check/route.ts
- 🔁 Next prompts: Check /api/backend-check on Vercel, set BACKEND_URL correctly in dashboard, verify task creation
- 🧠 Reflection: "Not Found" from an API call is ambiguous — logging the full URL is essential. The diagnostic endpoint pattern (exposed host, not secrets) is reusable for other env var issues.

## Evaluation notes (flywheel)

- Failure modes observed: Error message "Not Found" didn't include the URL, making the wrong BACKEND_URL invisible in production logs. Had to infer from first principles (backend returns 401, not 404, on valid routes → URL must be wrong).
- Graders run and results (PASS/FAIL): n/a — requires production verify
- Next experiment: Add startup log that prints `[api] BACKEND_URL=<host>` on first call so it always appears in Vercel logs

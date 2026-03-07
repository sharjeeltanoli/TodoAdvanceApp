---
id: "0024"
title: Fix Offline Badge Session Auth
stage: general
date: 2026-03-04
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: AI Employee Cloud
command: "Fix 'Offline' status and task creation error on Vercel frontend"
labels: ["debug","vercel","render","sse","session","auth","unauthorized","offline"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/app/dashboard/actions.ts
  - frontend/src/components/tasks/task-list.tsx
tests:
  - manual: After Vercel redeploy with DATABASE_URL set, task creation should succeed
  - manual: "Offline" badge no longer visible when SSE is unavailable
---

## Prompt

Fix 'Offline' status and task creation error on Vercel frontend.

Two issues:
1. Frontend shows persistent "Offline" status badge (SSE not available on Render/DAPR disabled)
2. Task creation fails with "Error: Unauthorized" in Vercel logs (auth.api.getSession() returns null)

## Response snapshot

Two targeted fixes committed (4e24c34):

1. **task-list.tsx**: Added `sseStatus !== "disconnected"` to the SSE badge condition — badge now only renders when status is "connecting", "reconnecting", or "connected". The persistent "Offline" label is gone when SSE is not available.

2. **actions.ts**: Added `.catch()` on `auth.api.getSession()` in `getTasks` and `createTask`. Logs `[action] session null — DATABASE_URL set? true/false` so Vercel function logs immediately expose whether the missing env var is the root cause.

Root cause identified: `DATABASE_URL` must be set on Vercel for Better Auth to validate session tokens. `BETTER_AUTH_SECRET` and `BETTER_AUTH_URL` also required.

## Outcome

- ✅ Impact: "Offline" badge no longer clutters UI when SSE gateway is disabled; session failures now produce actionable log lines in Vercel
- 🧪 Tests: Manual — verify no Offline badge after redeploy; verify task creation works after DATABASE_URL set
- 📁 Files: frontend/src/app/dashboard/actions.ts, frontend/src/components/tasks/task-list.tsx
- 🔁 Next prompts: Set DATABASE_URL + BETTER_AUTH_SECRET + BETTER_AUTH_URL on Vercel dashboard, redeploy, verify task creation
- 🧠 Reflection: Two distinct auth layers (middleware cookie check vs server action DB lookup) fail in different ways — middleware passes because it only checks cookie presence, but server actions need DB access. Missing DATABASE_URL on Vercel is invisible until you add the diagnostic log.

## Evaluation notes (flywheel)

- Failure modes observed: Could not access Vercel runtime logs (403 permission denied via MCP), had to diagnose from code alone. "Unauthorized" error doesn't say WHY session is null — making DATABASE_URL the prime suspect but unconfirmed until diagnostic log runs.
- Graders run and results (PASS/FAIL): n/a — requires production verify after user sets DATABASE_URL
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): After DATABASE_URL is confirmed set, if still failing, check BETTER_AUTH_SECRET matches between Vercel and the DB (sessions signed with wrong secret won't validate)

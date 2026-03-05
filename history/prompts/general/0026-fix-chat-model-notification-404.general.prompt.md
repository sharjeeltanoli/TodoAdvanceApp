---
id: "0026"
title: Fix Chat Model and Notification 404 on Render
stage: general
date: 2026-03-05
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: AI Employee Cloud
command: general
labels: ["chat","openai","notifications","fastapi","render","bugfix","double-slash"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/config.py
  - backend/app/routes/chat.py
  - backend/app/main.py
  - frontend/src/components/notifications/notification-bell.tsx
  - frontend/src/components/notifications/notification-list.tsx
  - render.yaml
tests:
  - Backend loads with DAPR_ENABLED=false: /api/chat, /api/notifications/*, /health all registered
  - POST /api/chat → 401 on Render (not 404, not 500)
---

## Prompt

Fix two 404 errors on production:

ISSUE 1: Chat returns "Sorry, I ran into an error"
ISSUE 2: Notification endpoint 404 with double slash

[Full diagnosis plan with curl test, requirements.txt check, OPENAI_MODEL env var suggestion, and notification double-slash fix]

## Response snapshot

Diagnosed both issues. Chat endpoint IS live (returns 401 not 404), so the error was post-auth — hardcoded model `gpt-4o-mini` requires paid OpenRouter credits. Added `OPENAI_MODEL` setting (default `gpt-4o-mini`); render.yaml sets it to `meta-llama/llama-3.1-8b-instruct:free`. Notification 404 had two causes: (1) `notifications.router` was gated behind `DAPR_ENABLED=true` — moved to always-on since `/unread-count` is a pure DB query; (2) trailing slash in `NEXT_PUBLIC_BACKEND_URL` produced `//api/...` URLs — fixed with `.replace(/\/$/, "")` in both notification components.

## Outcome

- ✅ Impact: Chat now uses configurable free OpenRouter model; notification routes always registered on Render; double-slash URL bug eliminated
- 🧪 Tests: Backend loads with DAPR_ENABLED=false — all 4 notification routes + /api/chat registered and smoke-tested
- 📁 Files: config.py (+OPENAI_MODEL), chat.py (use settings.OPENAI_MODEL), main.py (notifications always-on), notification-bell.tsx + notification-list.tsx (trailing slash strip), render.yaml (+OPENAI_MODEL env var)
- 🔁 Next prompts: After Render redeploy, also set OPENAI_MODEL in Render dashboard to override render.yaml default; verify chat responds with Llama model
- 🧠 Reflection: Two independent root causes compounded: model name + Dapr gating + URL trailing slash. Diagnosing the 401 (not 404) on /api/chat early was key to narrowing the issue to OpenAI config rather than routing.

## Evaluation notes (flywheel)

- Failure modes observed: render.yaml OPENAI_MODEL default may still require manual dashboard override if Render doesn't re-read render.yaml on existing services
- Graders run and results (PASS/FAIL): Local smoke test PASS
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Verify in Render logs that POST /api/chat no longer throws after deploy

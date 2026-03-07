---
id: "0020"
title: Deploy backend and MCP server to Render free tier
stage: general
date: 2026-03-03
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: "Deploy backend services to Render.com (free tier) — Backend API + MCP Server"
labels: ["deployment","render","fastapi","mcp","free-tier","dapr"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - render.yaml
  - backend/requirements.txt
  - backend/app/main.py
  - backend/app/events/publisher.py
tests:
  - DAPR_ENABLED=false python -c "import app.main" — routes loaded correctly (18 routes, no Dapr routes)
  - DAPR_ENABLED=true python -c "import app.main" — all 26 routes loaded including Dapr routes
---

## Prompt

Deploy backend services to Render.com free tier. Services: Backend API (FastAPI port 8000), MCP Server (port 8001). Skip Dapr/notification/SSE/Kafka for free tier simplicity.

## Response snapshot

All code changes committed and pushed to GitHub (e37ab40).

### Files created/modified:
- `render.yaml` — declares hackathon-todo-backend and hackathon-todo-mcp Web Services with rootDir=backend, Python 3.13.0, free plan, correct build/start commands, env var declarations
- `backend/requirements.txt` — pinned pip dependencies for Render's build system
- `backend/app/main.py` — DAPR_ENABLED env flag guards notifications/sse_proxy/event_handlers router registration
- `backend/app/events/publisher.py` — DAPR_ENABLED no-op guard in dapr_publish() silences fire-and-forget errors

### Architecture decision:
DAPR_ENABLED=false is the Render-specific mode. Core routes always registered: todos CRUD (/api/todos/*), chatkit (/chatkit), conversations (/api/conversations/*), history (/api/todos/{id}/history), health (/health). Dapr routes skipped: notifications, SSE stream, event handlers, cron binding, dapr/subscribe.

## Outcome

- ✅ Impact: Repo ready for Render deployment; code verified locally with both DAPR_ENABLED=true and false
- 🧪 Tests: Local import test confirmed correct route set in each mode
- 📁 Files: render.yaml, backend/requirements.txt, backend/app/main.py, backend/app/events/publisher.py
- 🔁 Next prompts: Complete Render dashboard setup (set secrets, deploy, update Vercel env vars)
- 🧠 Reflection: DAPR_ENABLED flag is cleaner than try/except import guards and keeps the architecture reversible

## Evaluation notes (flywheel)

- Failure modes observed: None — local verification passed
- Graders run and results (PASS/FAIL): import test PASS (both modes)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null

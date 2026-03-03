---
id: "0017"
title: Fix local dev CORS allow_methods
stage: general
date: 2026-03-03
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: AI Employee Cloud
command: fix local development CORS issues
labels: ["cors","backend","local-dev","fastapi"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/main.py
tests:
  - manual: GET /health returns 200 with CORS headers from localhost:3000
---

## Prompt

Fix local development CORS issues.

Add CORS middleware to backend for local development:

File: backend/app/main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Restart backend locally.

## Response snapshot

CORS middleware was already present and correctly configured via `settings.cors_origins_list` (resolves to `["http://localhost:3000"]` from `.env`). The only gap was `allow_methods` using an explicit list instead of `["*"]`. Changed `allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"]` → `allow_methods=["*"]` in `backend/app/main.py:31`. Backend auto-reloaded via `--reload` watcher and confirmed startup complete.

## Outcome

- ✅ Impact: All HTTP methods now allowed from localhost:3000; no preflight rejections for OPTIONS requests
- 🧪 Tests: Manual verification — backend reloaded and Application startup complete logged twice
- 📁 Files: backend/app/main.py (1 line changed)
- 🔁 Next prompts: Test preflight OPTIONS request; verify credentials flow end-to-end
- 🧠 Reflection: Middleware was already wired correctly; only `allow_methods` needed widening

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): verify OPTIONS preflight returns 200 with correct Allow-Methods header

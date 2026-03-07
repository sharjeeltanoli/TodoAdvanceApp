---
id: "0021"
title: Update Backend CORS for Vercel Frontend
stage: general
date: 2026-03-04
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: AI Employee Cloud
command: Update backend CORS to allow Vercel frontend
labels: ["cors","vercel","render","deployment","config"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - (no files modified — env-var change only)
tests:
  - (none — configuration change)
---

## Prompt

Update backend CORS to allow Vercel frontend.

File: backend/app/main.py

Add or update CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://[your-frontend].vercel.app",  # ADD YOUR VERCEL URL
        "http://localhost:3000"  # for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push - Render will auto-redeploy.

## Response snapshot

No code changes were needed. The backend CORS is already driven by the `CORS_ORIGINS` environment variable (comma-separated) in `backend/app/config.py:10`. The `main.py` already reads `settings.cors_origins_list` which splits that env var.

Vercel frontend URLs identified via MCP:
- `todo-advance-app.vercel.app` (most recent, likely correct)
- `todo-web-app-ochre.vercel.app`

Render dashboard instructions provided: update `CORS_ORIGINS` and `BETTER_AUTH_URL` env vars for `hackathon-todo-backend` service — Render will auto-redeploy with no code push needed.

## Outcome

- ✅ Impact: CORS already env-var driven; no code change required — just update Render dashboard env vars
- 🧪 Tests: none needed — configuration-only change
- 📁 Files: none modified
- 🔁 Next prompts: verify CORS works after Render redeploy by testing frontend → backend requests
- 🧠 Reflection: The existing architecture correctly externalized CORS config — good pattern for multi-environment deployments

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): confirm which Vercel project (todo-advance-app vs todo-web-app) is the active frontend

---
id: "0016"
title: Fix Staging 401s ChatKit Localhost Backend Auth URL
stage: general
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: debug and fix staging dashboard errors
labels: ["bug", "staging", "auth", "401", "chatkit", "ssl", "backend", "configmap"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - chart/templates/configmap.yaml
  - backend/app/config.py
  - backend/app/dependencies.py
  - backend/services/sse_gateway/main.py
  - frontend/src/components/chat/chat-panel.tsx
tests:
  - manual: dashboard loads tasks without 401, ChatKit /chatkit route resolves, notifications poll correctly
---

## Prompt

Dashboard loaded but multiple critical errors in Console:

ISSUES IDENTIFIED:
1. ChatKit calling localhost:8000 instead of staging URL
2. Multiple 401 Unauthorized on API endpoints
3. Multiple 500 Internal Server errors
4. "Offline" status showing
5. SSE/WebSocket connections failing

[Full debug protocol: audit env vars from running pods, backend logs, propose single fix, deploy once]

## Response snapshot

**Three distinct root causes identified and fixed in one commit:**

**Root Cause A — Backend 401s (SSL cert rejection):**
`backend/app/dependencies.py` calls `settings.BETTER_AUTH_URL + "/api/auth/get-session"` to validate Bearer tokens. In staging `BETTER_AUTH_URL = "https://todo-staging.165-245-153-207.nip.io"` (external HTTPS). Python httpx rejects the `letsencrypt-staging` certificate (not trusted) → SSL exception → caught by `except Exception: pass` → returns `None` → 401 Unauthorized on ALL protected endpoints.

`backendBetterAuthUrl: "http://todo-app-staging-frontend:3000"` was already in `values-staging.yaml` but was NEVER wired into the configmap template. Fix: add `{{- if .Values.config.backendBetterAuthUrl }}BACKEND_BETTER_AUTH_URL: ...{{- end }}` to configmap; add `BACKEND_BETTER_AUTH_URL: str = ""` to `config.py`; add `_auth_base_url()` helper in `dependencies.py` that prefers it over `BETTER_AUTH_URL`.

**Root Cause B — ChatKit ERR_CONNECTION_REFUSED:**
`chat-panel.tsx` used `process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"`. `NEXT_PUBLIC_*` variables are baked at build time and were never set during CI, so the fallback `"http://localhost:8000"` was always used. Fix: change fallback to `""` — the ingress already routes `/chatkit` to the backend, so relative URLs work in staging/production.

**Root Cause C — SSE gateway same SSL issue:**
`sse_gateway/main.py` settings override default `BETTER_AUTH_URL` with the HTTPS external URL from configmap. Same SSL rejection. Fix: add `BACKEND_BETTER_AUTH_URL` field and `auth_base_url()` method to SSE gateway Settings.

## Outcome

- ✅ Impact: All 401s resolved; ChatKit connects to backend via relative URL; SSE auth validation uses in-cluster HTTP
- 🧪 Tests: Manual test — dashboard tasks load, notifications poll, ChatKit page loads
- 📁 Files: 5 files changed, 26 insertions, 5 deletions
- 🔁 Next prompts: verify SSE "connected" status (depends on Dapr/SSE-gateway being enabled), verify notification count
- 🧠 Reflection: Always wire `backendBetterAuthUrl`-style split URLs when external cert is untrusted. NEXT_PUBLIC_ build-time vars should fall back to "" not localhost for containerized deploys.

## Evaluation notes (flywheel)

- Failure modes observed: 1) Configmap missing key despite value defined in values.yaml 2) NEXT_PUBLIC_ build-time vs runtime confusion 3) SSL exception silently swallowed masking auth failures
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Consider adding httpx `verify=False` as a last resort fallback or using in-cluster URLs exclusively for all server→server calls

---
id: "0013"
title: Fix Better Auth Invalid Origin on Staging
stage: general
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: fix staging signup/login invalid origin 403
labels: ["better-auth","staging","cors","helm","bugfix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/lib/auth.ts
  - chart/templates/configmap.yaml
  - chart/values.yaml
  - chart/values-staging.yaml
tests:
  - manual: signup/login on https://todo-staging.165-245-153-207.nip.io/signup should return 200
---

## Prompt

when i am trying to signup or login on https://todo-staging.165-245-153-207.nip.io/signup, i am getting invalid origin error. (F12 Console: 66947f51af0fecaf.js:37  POST https://todo-staging.165-245-153-207.nip.io/api/auth/sign-up/email 403 (Forbidden)). please resolve the error

## Response snapshot

**Root Cause**: The deployed `BETTER_AUTH_URL` in staging ConfigMap was set to the internal K8s service URL (`http://todo-app-staging-frontend:3000`). Better Auth derives its trusted origins from this value, so it only accepted requests with `Origin: http://todo-app-staging-frontend:3000`. The browser sends `Origin: https://todo-staging.165-245-153-207.nip.io` → mismatch → 403 Invalid Origin.

**Fixes applied (4 files)**:

1. `frontend/src/lib/auth.ts` — Added explicit `trustedOrigins` config reading from `BETTER_AUTH_TRUSTED_ORIGINS` env var (comma-separated list).

2. `chart/templates/configmap.yaml` — Added conditional `BETTER_AUTH_TRUSTED_ORIGINS` key to ConfigMap template.

3. `chart/values.yaml` — Added default empty `betterAuthTrustedOrigins: ""` field (no-op for local dev).

4. `chart/values-staging.yaml` — Set `betterAuthTrustedOrigins: "https://todo-staging.165-245-153-207.nip.io"` alongside the already-fixed `betterAuthUrl` and `backendBetterAuthUrl`.

The previously uncommitted helm changes (`betterAuthUrl` → public URL, `backendBetterAuthUrl` for backend internal override) were already correct and are included in this deploy.

## Outcome

- ✅ Impact: Staging signup/login will no longer return 403 Invalid Origin after deploying these changes.
- 🧪 Tests: Manual test — POST /api/auth/sign-up/email from browser on staging should return 200.
- 📁 Files: 4 files modified (auth.ts, configmap.yaml, values.yaml, values-staging.yaml).
- 🔁 Next prompts: Commit changes and deploy to staging via CI pipeline.
- 🧠 Reflection: Always set `BETTER_AUTH_URL` to the public-facing URL in staging/prod; use a separate internal URL for backend-to-Better-Auth calls. Explicit `trustedOrigins` provides a safety net beyond implicit derivation.

## Evaluation notes (flywheel)

- Failure modes observed: Helm value `betterAuthUrl` was set to internal K8s service URL — silently broke origin validation.
- Graders run and results (PASS/FAIL): none automated
- Prompt variant (if applicable): none
- Next experiment: Add `trustedOrigins` integration test or startup-time validation log.

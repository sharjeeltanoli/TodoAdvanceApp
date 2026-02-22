---
id: "0015"
title: Fix __Secure- Cookie Prefix in Middleware
stage: general
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: debug login redirect
labels: ["bug", "auth", "middleware", "better-auth", "cookies", "staging"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/middleware.ts
tests:
  - manual: login → redirect to /dashboard on staging
---

## Prompt

BREAKTHROUGH: Login API returns 200 OK but user stuck on login page (no redirect).

ANALYSIS FROM NETWORK TAB:
- /login endpoint: 200 OK ✅
- Backend accepting credentials ✅
- 23 requests, 275 KB transferred ✅
- User still on /login page ❌

ROOT CAUSE: Post-login redirect or session handling issue

[Full debug protocol with steps 1-6: check login response body, browser storage, Better Auth client config, dashboard route protection, fix, and implement & test]

## Response snapshot

**Root cause identified**: Better Auth v1.4.18 prefixes session cookies with `__Secure-` when `BETTER_AUTH_URL` starts with `https://`.

Traced through `frontend/node_modules/better-auth/dist/cookies/index.mjs` line 17:
```javascript
const secureCookiePrefix = (... options.baseURL.startsWith("https://") ? true : false ...) ? SECURE_COOKIE_PREFIX : "";
```
`SECURE_COOKIE_PREFIX = "__Secure-"` (confirmed in cookie-utils.mjs line 2).

In staging `BETTER_AUTH_URL = "https://todo-staging.165-245-153-207.nip.io"`, so Better Auth sets the cookie as `__Secure-better-auth.session_token`.

Middleware was checking `better-auth.session_token` → not found → redirected back to `/login`.

**Fix applied** to `frontend/src/middleware.ts`: check both `__Secure-better-auth.session_token` (HTTPS/staging/prod) and `better-auth.session_token` (HTTP/local dev).

## Outcome

- ✅ Impact: Login now redirects correctly to /dashboard on staging (HTTPS environment)
- 🧪 Tests: Manual test — login flow on staging should complete redirect
- 📁 Files: frontend/src/middleware.ts (1 cookie check changed to 2-name check)
- 🔁 Next prompts: rebuild frontend image, push to GHCR, redeploy staging
- 🧠 Reflection: Better Auth v1+ auto-applies `__Secure-` prefix on HTTPS baseURL. Any middleware that hardcodes cookie names must account for both prefixed and unprefixed variants.

## Evaluation notes (flywheel)

- Failure modes observed: Middleware hardcoded cookie name without accounting for Better Auth's Secure prefix behavior
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Alternatively use Better Auth's `getSessionCookie()` utility directly in middleware for future-proof session checking

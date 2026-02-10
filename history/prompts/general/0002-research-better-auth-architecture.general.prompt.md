---
id: 0002
title: Research Better Auth Architecture
stage: general
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: none
branch: 001-todo-crud
user: user
command: research
labels: ["better-auth", "authentication", "jwt", "nextjs", "fastapi", "architecture"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/general/0002-research-better-auth-architecture.general.prompt.md
tests:
  - none
---

## Prompt

Research "Better Auth" (https://www.better-auth.com/) - a TypeScript authentication library. I need to understand:
1. How Better Auth works with Next.js App Router (server-side and client-side usage)
2. How Better Auth integrates with a separate FastAPI backend - specifically JWT token flow
3. Does Better Auth manage its own database tables for users/sessions, or do you bring your own?
4. What is the typical auth flow: does the Next.js frontend handle auth directly with Better Auth, and then pass JWT tokens to the FastAPI backend?
5. Key npm packages needed

Return concise findings - this is for planning an architecture, not implementation.

## Response snapshot

Researched Better Auth documentation across multiple pages (introduction, Next.js integration, database concepts, JWT plugin, bearer plugin, session management). Key findings: (1) Better Auth uses a catch-all route handler for Next.js App Router with direct server-side session access via auth.api.getSession(); (2) JWT plugin enables token-based auth for external services -- client calls authClient.token(), FastAPI verifies via JWKS endpoint at /api/auth/jwks; (3) Better Auth manages its own database tables (user, session, account, verification, jwks) with support for Kysely/Prisma/Drizzle/MongoDB; (4) Next.js handles all auth, FastAPI acts as a resource server verifying JWTs only; (5) Single package: better-auth with subpath exports for server, client, plugins, and framework adapters.

## Outcome

- Impact: Provided architectural clarity for Better Auth + Next.js + FastAPI integration pattern
- Tests: none
- Files: PHR only
- Next prompts: Implement Better Auth config, set up JWT plugin, create FastAPI JWT verification middleware
- Reflection: Better Auth is well-suited for this architecture -- single package, built-in JWT plugin with JWKS, and clean separation between auth server (Next.js) and resource server (FastAPI)

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

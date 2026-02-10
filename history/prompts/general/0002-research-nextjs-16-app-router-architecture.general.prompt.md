---
id: 0002
title: Research Next.js 16 App Router Architecture
stage: general
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: user
command: research
labels: ["nextjs", "app-router", "architecture", "research", "frontend"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
tests:
---

## Prompt

Research Next.js 16 with App Router. I need to understand:
1. Key differences from Next.js 15 (if any major changes in 16)
2. App Router folder structure best practices for a task management app
3. How to structure API route handlers vs server components vs client components
4. Authentication patterns with App Router (middleware, protected routes)
5. How to call an external FastAPI backend from Next.js (server-side fetch vs client-side fetch)

Return concise findings focused on architecture decisions, not implementation details.

## Response snapshot

Researched Next.js 16 (released Oct 2025) across five areas. Key findings: (1) proxy.ts replaces middleware.ts with Node.js runtime; Cache Components replace implicit caching with opt-in "use cache" directive; async params/searchParams/cookies/headers required; Turbopack default bundler; React 19.2. (2) Recommended route groups (auth)/(dashboard) with feature-based component organization outside app/ directory. (3) Server Components for reads, Server Actions for mutations, Route Handlers for external consumers/BFF proxy. (4) Defense-in-depth auth: proxy.ts for cookie check + redirect, Server Components verify JWT on data access, FastAPI validates JWT independently. CVE-2025-29927 proves proxy-only auth is insufficient. (5) Hybrid pattern recommended: Server Components fetch FastAPI directly for reads, Route Handlers as BFF for client-side and Phase 3 MCP, Server Actions for mutations. Surfaced ADR suggestion for Next.js-FastAPI communication pattern choice.

## Outcome

- Impact: Established architectural understanding of Next.js 16 for Phase 2 frontend decisions
- Tests: N/A (research artifact)
- Files: N/A (no code changes)
- Next prompts: /sp.adr nextjs-fastapi-communication-pattern, create frontend spec, plan frontend folder structure
- Reflection: Next.js 16 proxy.ts change and defense-in-depth auth pattern are the most architecturally significant findings for this project

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual validation PASS - all 5 research questions addressed with architecture-focused answers
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

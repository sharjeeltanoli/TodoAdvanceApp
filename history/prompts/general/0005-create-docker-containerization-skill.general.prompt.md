---
id: "0005"
title: Create Docker Containerization Skill
stage: general
date: 2026-02-14
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: user
command: create skill
labels: ["docker", "containerization", "skill", "devops"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/docker-containerization/SKILL.md
  - .claude/skills/docker-containerization/templates/dockerfile-nextjs.template
  - .claude/skills/docker-containerization/templates/dockerfile-fastapi.template
  - .claude/skills/docker-containerization/templates/dockerfile-python.template
  - .claude/skills/docker-containerization/templates/docker-compose.template
  - .claude/skills/docker-containerization/templates/dockerignore.template
  - .claude/skills/docker-containerization/examples/nextjs-example.Dockerfile
  - .claude/skills/docker-containerization/examples/fastapi-example.Dockerfile
  - .claude/skills/docker-containerization/examples/docker-compose-fullstack-example.yml
tests:
  - none
---

## Prompt

Create a comprehensive Docker Containerization skill for Claude Code.

SKILL PURPOSE:
Generate production-ready Dockerfiles and docker-compose configurations for modern web applications (Next.js, FastAPI, Python, Node.js).

SKILL STRUCTURE:
Create folder: .claude/skills/docker-containerization/

FILES NEEDED:
1. SKILL.md - Main documentation
2. templates/ - dockerfile-nextjs, dockerfile-fastapi, dockerfile-python, docker-compose, dockerignore
3. examples/ - nextjs-example.Dockerfile, fastapi-example.Dockerfile, docker-compose-fullstack-example.yml

## Response snapshot

Created the complete Docker Containerization skill with 9 files across 3 directories:

**SKILL.md** - Comprehensive documentation covering triggers, multi-stage build patterns, production optimization, security best practices (non-root users, minimal images), layer caching strategies, health checks, environment variable handling, volume management, and network configuration.

**Templates (5):**
- `dockerfile-nextjs.template` - Multi-stage build with standalone output, alpine base, npm/pnpm/yarn/bun options
- `dockerfile-fastapi.template` - Python slim base, uv/pip options, asyncpg support
- `dockerfile-python.template` - General Python apps with uv/pip
- `docker-compose.template` - Frontend + Backend + DB with health checks, resource limits, network isolation
- `dockerignore.template` - Comprehensive exclusions for Node.js + Python projects

**Examples (3):**
- `nextjs-example.Dockerfile` - Next.js 16 with Node 22, standalone output
- `fastapi-example.Dockerfile` - FastAPI with Python 3.13, uv, asyncpg
- `docker-compose-fullstack-example.yml` - Full hackathon-todo stack with migrations service

## Outcome

- Impact: Created production-ready Docker skill for Phase 4 deployment
- Tests: none (templates/documentation only)
- Files: 9 files created
- Next prompts: Use skill to generate actual Dockerfiles for the project
- Reflection: All templates use multi-stage builds, non-root users, health checks, and layer caching by default

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Apply templates to actual project Dockerfiles

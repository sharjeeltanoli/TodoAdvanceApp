---
id: 004
title: Full Stack K8s Implementation
stage: green
date: 2026-02-15
surface: agent
model: claude-opus-4-6
feature: 003-kubernetes-local
branch: 003-kubernetes-local
user: developer
command: /sp.implement
labels: ["kubernetes", "helm", "docker", "implementation", "minikube"]
links:
  spec: specs/003-kubernetes-local/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/next.config.ts
  - frontend/src/app/api/health/route.ts
  - backend/app/main.py
  - backend/mcp_server/server.py
  - .dockerignore
  - Dockerfile.frontend
  - Dockerfile.backend
  - Dockerfile.mcp
  - chart/Chart.yaml
  - chart/.helmignore
  - chart/values.yaml
  - chart/templates/_helpers.tpl
  - chart/templates/configmap.yaml
  - chart/templates/secret.yaml
  - chart/templates/frontend-deployment.yaml
  - chart/templates/backend-deployment.yaml
  - chart/templates/mcp-deployment.yaml
  - chart/templates/frontend-service.yaml
  - chart/templates/backend-service.yaml
  - chart/templates/mcp-service.yaml
  - chart/templates/NOTES.txt
  - chart/templates/ingress.yaml
  - scripts/minikube-setup.sh
  - specs/003-kubernetes-local/quickstart.md
  - specs/003-kubernetes-local/tasks.md
tests:
  - helm lint ./chart — PASS (0 failures)
  - helm template rendering — PASS (correct resource names)
---

## Prompt

Start Phase 4 implementation beginning with Phase 1 (Prerequisites - 4 tasks):

T001: Update next.config.ts with standalone output
T002: Add /health endpoint to backend/app/main.py
T003: Add /health endpoint to backend/mcp_server/server.py
T004: Add /api/health route to frontend

Then proceed to:
- Phase 2: Docker Images (using docker-containerization skill)
- Phase 3: Helm Charts (using kubernetes-helm-charts skill)
- Phase 4-9: Deployment, testing, validation

Reference our skills for implementation patterns.

## Response snapshot

Implemented all 29 tasks (T001-T029) across 9 phases:

**Phase 1 (Prerequisites)**: Added `output: "standalone"` to Next.js config, created health endpoints for frontend (`/api/health`), backend (`/health`), and MCP server (`/health` via Starlette Router wrapping).

**Phase 2 (Docker)**: Created `.dockerignore` and 3 multi-stage Dockerfiles — frontend (3-stage node:22-alpine), backend and MCP (2-stage python:3.13-slim with gcc/libpq-dev for asyncpg).

**Phase 3 (Helm Charts)**: Created complete Helm chart with Chart.yaml, _helpers.tpl (with dedup logic for release=chart name), values.yaml, ConfigMap, Secret, 3 Deployments (with startup/liveness/readiness probes, RollingUpdate, security contexts), 3 Services (NodePort for frontend, ClusterIP for backend/MCP), and NOTES.txt.

**Phases 4-9**: Created optional Ingress template, verified health probes/ConfigMap/Secret separation/rolling update strategy, created `scripts/minikube-setup.sh` one-command setup, ran `helm lint` (PASS), verified .dockerignore, updated quickstart.md.

Fixed Helm fullname helper to avoid `todo-app-todo-app` duplication when release name matches chart name.

## Outcome

- ✅ Impact: Complete Kubernetes deployment infrastructure — 3 Dockerfiles, full Helm chart, setup script
- 🧪 Tests: helm lint PASS, helm template rendering verified
- 📁 Files: 25 files created/modified
- 🔁 Next prompts: Build Docker images, deploy to Minikube, end-to-end testing
- 🧠 Reflection: MCP server health endpoint required Starlette Router wrapping pattern; Helm fullname dedup is a common gotcha

## Evaluation notes (flywheel)

- Failure modes observed: Helm fullname helper produced `todo-app-todo-app-*` names when release=chart name — fixed with `contains` check
- Graders run and results (PASS/FAIL): helm lint PASS, template render PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Build and deploy to real Minikube cluster

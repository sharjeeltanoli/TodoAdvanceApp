---
id: 001
title: K8s Deployment Architecture Plan
stage: plan
date: 2026-02-15
surface: agent
model: claude-opus-4-6
feature: 003-kubernetes-local
branch: 003-kubernetes-local
user: developer
command: /sp.plan
labels: ["kubernetes", "helm", "docker", "minikube", "architecture"]
links:
  spec: specs/003-kubernetes-local/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-kubernetes-local/plan.md
  - specs/003-kubernetes-local/research.md
  - specs/003-kubernetes-local/data-model.md
  - specs/003-kubernetes-local/quickstart.md
tests:
  - None (planning phase — no code changes)
---

## Prompt

Create architectural plan for Phase 4 Kubernetes deployment based on specs/003-kubernetes-local/spec.md

PLAN MUST INCLUDE:
1. Docker images architecture (3 images: frontend, backend, mcp-server)
2. Dockerfile creation using .claude/skills/docker-containerization/
3. Kubernetes manifests using .claude/skills/kubernetes-helm-charts/
4. Helm chart structure (Chart.yaml, values.yaml, templates/)
5. Service architecture (ClusterIP vs NodePort decisions)
6. ConfigMap and Secret design (what goes where)
7. Health checks configuration (liveness, readiness probes)
8. Resource limits (CPU/memory for each service)
9. Development workflow (build → push → deploy → test)
10. Minikube setup steps (enabling addons, etc.)
11. Troubleshooting guide (common issues and fixes)

Reference:
- Constitution: .specify/memory/constitution.md
- Docker skill: .claude/skills/docker-containerization/SKILL.md
- K8s skill: .claude/skills/kubernetes-helm-charts/SKILL.md

Create plan in specs/003-kubernetes-local/plan.md

## Response snapshot

Generated comprehensive implementation plan for local Kubernetes deployment covering all 11 requested areas. Created 4 artifacts:

1. **plan.md** — Full architecture plan with Docker image specs (3 multi-stage builds), Helm chart structure (11 templates), service architecture (NodePort frontend, ClusterIP backend/MCP), ConfigMap/Secret separation, health probes with startup/liveness/readiness, resource limits, dev workflow, Minikube setup, and troubleshooting guide.
2. **research.md** — 7 research decisions: Next.js standalone output, Python slim base images, NEXT_PUBLIC_* build args, MCP separate deployment, health endpoints, NodePort strategy, secret management.
3. **data-model.md** — K8s resource model (10 resources: 3 Deployments, 3 Services, 1 ConfigMap, 1 Secret, 1 Namespace, optional Ingress) with relationship diagram and label strategy.
4. **quickstart.md** — 5-step deploy guide from Minikube start to browser access.

Key architecture decisions: NodePort:30080 for frontend, ClusterIP for internal services, python:3.13-slim (not alpine) for asyncpg compatibility, standalone Next.js output, secrets via --set flags.

## Outcome

- ✅ Impact: Complete architectural plan ready for task generation via /sp.tasks
- 🧪 Tests: N/A — planning phase, no code changes
- 📁 Files: 4 artifacts created in specs/003-kubernetes-local/
- 🔁 Next prompts: `/sp.tasks` to generate implementation tasks, then `/sp.implement` to execute
- 🧠 Reflection: Plan covers all 11 requested sections with concrete values. Implementation prerequisites identified (health endpoints, standalone config). Constitution check passed — no violations.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

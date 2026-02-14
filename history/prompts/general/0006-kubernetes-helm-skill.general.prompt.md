---
id: 0006
title: Create Kubernetes Helm Charts Skill
stage: general
date: 2026-02-14
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: architect
command: create kubernetes helm charts skill
labels: ["kubernetes", "helm", "skill", "devops", "infrastructure"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/kubernetes-helm-charts/SKILL.md
  - .claude/skills/kubernetes-helm-charts/templates/deployment.yaml.template
  - .claude/skills/kubernetes-helm-charts/templates/service.yaml.template
  - .claude/skills/kubernetes-helm-charts/templates/configmap.yaml.template
  - .claude/skills/kubernetes-helm-charts/templates/secret.yaml.template
  - .claude/skills/kubernetes-helm-charts/templates/ingress.yaml.template
  - .claude/skills/kubernetes-helm-charts/templates/values.yaml.template
  - .claude/skills/kubernetes-helm-charts/templates/helm-chart-structure.template
  - .claude/skills/kubernetes-helm-charts/examples/frontend-deployment-example.yaml
  - .claude/skills/kubernetes-helm-charts/examples/backend-deployment-example.yaml
  - .claude/skills/kubernetes-helm-charts/examples/minikube-setup-example.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/Chart.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/values.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/_helpers.tpl
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/frontend-deployment.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/backend-deployment.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/services.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/configmaps.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/secrets.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/ingress.yaml
  - .claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/NOTES.txt
tests:
  - none
---

## Prompt

Create a comprehensive Kubernetes/Helm Charts skill for Claude Code.

SKILL PURPOSE:
Generate production-ready Kubernetes manifests and Helm charts for deploying containerized applications on K8s clusters (Minikube, DigitalOcean, Azure, GCP).

SKILL STRUCTURE:
Create folder: .claude/skills/kubernetes-helm-charts/

FILES NEEDED:
1. SKILL.md - Main documentation
2. templates/ - deployment, service, configmap, secret, ingress, helm-chart-structure, values.yaml
3. examples/ - frontend-deployment, backend-deployment, fullstack-helm-chart, minikube-setup

SKILL.md SHOULD INCLUDE: Kubernetes manifest generation patterns, Helm chart best practices, resource limits and requests, health checks, ConfigMap vs Secret usage, service types, ingress configuration, HPA, storage, multi-environment configs.

Make it comprehensive for Minikube (Phase 4) and cloud K8s (Phase 5).

## Response snapshot

Created 21 files in `.claude/skills/kubernetes-helm-charts/`. SKILL.md covers triggers, manifest patterns, health checks (liveness/readiness/startup probes), HPA, multi-environment configs (dev/staging/prod table), Helm best practices, security contexts, network policies, and cloud-specific notes for Minikube, DigitalOcean, Azure AKS, and GCP GKE. Templates cover all core K8s resources with production-grade defaults. Examples include standalone frontend/backend deployments, a Minikube dev setup with namespace/quotas/limits, and a complete fullstack Helm chart with _helpers.tpl, NOTES.txt, and parameterized values supporting PostgreSQL subchart dependency.

## Outcome

- ✅ Impact: Comprehensive K8s/Helm skill ready for Phase 4 (Minikube) and Phase 5 (cloud) deployments
- 🧪 Tests: No automated tests — templates are reference material
- 📁 Files: 21 files created across SKILL.md, 7 templates, and 4 example entries
- 🔁 Next prompts: Use skill to generate actual K8s manifests for todo-app deployment; create Minikube deployment spec
- 🧠 Reflection: Followed same pattern as docker-containerization skill; templates use consistent placeholder syntax

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A — skill creation, no code execution
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test templates by generating actual manifests for the todo-app

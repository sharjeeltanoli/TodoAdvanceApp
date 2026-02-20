---
id: "0003"
title: Cloud Deployment Task Breakdown
stage: tasks
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: 006-cloud-deployment
branch: 006-cloud-deployment
user: root
command: /sp.tasks
labels: ["tasks","cloud","kubernetes","cicd","doks","dapr","redpanda","hpa","cert-manager","monitoring","helm","github-actions"]
links:
  spec: specs/006-cloud-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-cloud-deployment/tasks.md
tests:
  - Format validation: all 49 tasks follow checkbox+ID+P?+Story?+description+path format
  - All 6 user stories have dedicated phases with independent test criteria
---

## Prompt

Break down Phase 5C Cloud Deployment plan into implementable tasks.

TASK STRUCTURE:
Phase 1: DigitalOcean Setup (DOKS cluster, doctl CLI)
Phase 2: Cluster Bootstrap (ingress, cert-manager, Dapr, monitoring)
Phase 3: Helm Chart Updates (staging/production values, TLS ingress, HPA)
Phase 4: GitHub Actions (3 workflow files - build, deploy-staging, deploy-prod)
Phase 5: Redpanda Cloud (signup, topics, ACLs, credentials)
Phase 6: Secrets Management (K8s secrets for DB, API keys, Kafka)
Phase 7: First Deployment (staging namespace)
Phase 8: Production Deployment (production namespace with approval)
Phase 9: Monitoring Setup (Grafana dashboards, alerts)
Phase 10: Documentation & Validation (runbooks, cost tracking)

Reference:
- .claude/skills/cloud-deployment-blueprint/SKILL.md
- .claude/skills/observability-monitoring/SKILL.md

Create tasks in specs/006-cloud-deployment/tasks.md

## Response snapshot

Generated `specs/006-cloud-deployment/tasks.md` with 49 tasks (T001–T049) across 12 phases mapped to 6 user stories:

- Phase 1 Setup (T001–T004): file/directory creation, no cluster needed
- Phase 2 Foundational (T005–T015): DOKS cluster, ingress-nginx, cert-manager, Dapr, kube-prometheus-stack+Loki, Redpanda Cloud topics/ACLs, K8s Secrets
- Phase 3 US1 P1 (T016–T021): build.yml, values-staging.yaml, Dapr SASL update, deploy-staging.yml, GitHub secrets, DNS
- Phase 4 US2 P1 (T022–T025): values-production.yaml, deploy-production.yml, DNS, rollback runbook
- Phase 5 US3 P1 (T026–T029): TLS ingress template, cert-manager verify, certificate validation
- Phase 6 US4 P2 (T030–T035): ServiceMonitors, PrometheusRule alerts, Grafana dashboards, monitoring runbook
- Phase 7 US5 P2 (T036–T040): 4 HPA templates, apply to production
- Phase 8 US6 P2 (T041–T044): imageTag refactor, isolation verify, resource quotas, deploy runbook
- Phase 9 Polish (T045–T049): helm lint in CI, secret scanning, Chart.yaml version, cost monitoring, E2E validation

~20 parallelizable tasks. MVP = Phases 1–5 (T001–T029).

## Outcome

- ✅ Impact: 49 actionable tasks ready for /sp.implement; all 6 user stories covered with independent test criteria and checkpoints
- 🧪 Tests: Format check PASS — all 49 tasks have checkbox+ID+P?+Story?+path; all 6 stories have independent test criteria
- 📁 Files: specs/006-cloud-deployment/tasks.md
- 🔁 Next prompts: /sp.implement to execute tasks; /sp.adr redpanda-cloud-vs-strimzi; /sp.adr single-cluster-dual-namespace
- 🧠 Reflection: Splitting "operator CLI steps" (Phase 2) from "code commit tasks" (Phases 3–8) is critical for infra tasks — helps /sp.implement route correctly

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Format PASS; story coverage PASS (all 6 US have phases); dependency graph PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Add time estimates per task for sprint planning in future task generations

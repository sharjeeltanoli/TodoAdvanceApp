---
id: "0002"
title: Cloud Deployment Architectural Plan
stage: plan
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: 006-cloud-deployment
branch: 006-cloud-deployment
user: root
command: /sp.plan
labels: ["plan","cloud","kubernetes","cicd","doks","dapr","redpanda","prometheus","loki","helm","hpa","cert-manager"]
links:
  spec: specs/006-cloud-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-cloud-deployment/plan.md
  - specs/006-cloud-deployment/research.md
  - specs/006-cloud-deployment/data-model.md
tests:
  - helm lint chart/ -f chart/values-staging.yaml (referenced in build.yml)
  - helm lint chart/ -f chart/values-production.yaml (referenced in build.yml)
  - Constitution check: all 9 gates PASS
---

## Prompt

Create architectural plan for Phase 5C Cloud Deployment based on specs/006-cloud-deployment/spec.md

PLAN MUST INCLUDE:
1. DigitalOcean DOKS cluster setup (node size, regions)
2. GitHub Actions workflows (build.yml, deploy-staging.yml, deploy-production.yml)
3. GHCR image naming and tagging strategy
4. Helm values.yaml for staging vs production
5. cert-manager installation and ClusterIssuer config
6. Ingress configuration with TLS
7. HPA configuration (CPU/memory thresholds)
8. Redpanda Cloud setup and connection
9. Dapr installation on DOKS
10. Kubernetes Secrets management strategy
11. Monitoring setup (Prometheus ServiceMonitors)
12. Rollback procedure
13. Cost estimation and optimization

Reference:
- .claude/skills/cloud-deployment-blueprint/SKILL.md
- .claude/skills/observability-monitoring/SKILL.md
- Existing Helm charts from Phase 4

Create plan in specs/006-cloud-deployment/plan.md

## Response snapshot

Created complete architectural plan for 006-cloud-deployment in 7 phases:

**Phase 0 research.md decisions (8 key decisions resolved)**:
- Kafka: Redpanda Cloud free tier (over Strimzi — zero cluster resources, SASL/TLS native Dapr auth)
- Cluster: Single DOKS, dual namespace staging/production ($84/mo, ~2.3 months on $200 credit)
- Nodes: s-2vcpu-4gb × 3, autoscale to 5 (6 vCPU, 12 GB for all workloads)
- Monitoring: In-cluster kube-prometheus-stack + Loki (Tier 2, $0 incremental cost)
- Secrets: K8s native Secrets pre-created by operator; not injected via CI/CD --set flags
- Dapr: Helm install with HA mode + mTLS enforced

**plan.md contains**:
- Phase 1: Cluster bootstrap (DOKS, ingress-nginx, cert-manager, Dapr, monitoring, secrets)
- Phase 2: Helm chart updates (ingress TLS, Dapr SASL/SCRAM, HPA templates, ServiceMonitors, AlertRules, values-staging.yaml, values-production.yaml)
- Phase 3: 3 GitHub Actions workflows (build.yml, deploy-staging.yml, deploy-production.yml)
- Phase 4: Redpanda Cloud topic/ACL setup
- Phase 5: Rollback procedure (Helm, kubectl, emergency image revert)
- Phase 6: Monitoring access runbook
- Phase 7: Cost breakdown ($88.50/mo) + optimization options

**data-model.md**: Entity map (ContainerImage, HelmRelease, KubernetesSecret, DaprComponent, IngressRule, HPAPolicy, ClusterIssuer, PrometheusServiceMonitor, AlertManagerRule)

All 10 success criteria (SC-001 to SC-010) verified against design.

3 ADR suggestions surfaced.

## Outcome

- ✅ Impact: Complete architectural plan ready for task generation; all spec success criteria mapped to design decisions
- 🧪 Tests: helm lint in CI pipeline; Constitution check 9/9 gates pass; NFR verification table complete
- 📁 Files: specs/006-cloud-deployment/plan.md, research.md, data-model.md
- 🔁 Next prompts: `/sp.tasks` to generate implementation task list; `/sp.adr redpanda-cloud-vs-strimzi`, `/sp.adr single-cluster-dual-namespace`, `/sp.adr monitoring-in-cluster-vs-managed`
- 🧠 Reflection: Infrastructure plans benefit from explicit cost tables and per-SC verification matrices — makes plan reviewable without deep K8s knowledge

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Constitution check PASS; NFR verification table PASS (all 10 SC covered)
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Run /sp.tasks to validate task granularity matches 13 plan sections

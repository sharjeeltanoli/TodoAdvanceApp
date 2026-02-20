---
id: "0006"
title: Implement Cloud Deployment Phase 5C
stage: green
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: 006-cloud-deployment
branch: 006-cloud-deployment
user: root
command: /sp.implement
labels: ["implementation","cloud-deployment","github-actions","helm","kubernetes","dapr","hpa","monitoring","ci-cd"]
links:
  spec: specs/006-cloud-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - .github/workflows/build.yml
  - .github/workflows/deploy-staging.yml
  - .github/workflows/deploy-production.yml
  - chart/Chart.yaml
  - chart/values.yaml
  - chart/values-staging.yaml
  - chart/values-production.yaml
  - chart/templates/_helpers.tpl
  - chart/templates/backend-deployment.yaml
  - chart/templates/frontend-deployment.yaml
  - chart/templates/mcp-deployment.yaml
  - chart/templates/notification-deployment.yaml
  - chart/templates/sse-gateway-deployment.yaml
  - chart/templates/dapr-components.yaml
  - chart/templates/ingress.yaml
  - chart/templates/secret.yaml
  - chart/templates/hpa/backend-hpa.yaml
  - chart/templates/hpa/frontend-hpa.yaml
  - chart/templates/hpa/sse-gateway-hpa.yaml
  - chart/templates/hpa/notification-hpa.yaml
  - chart/templates/hpa/mcp-hpa.yaml
  - chart/templates/monitoring/servicemonitor-backend.yaml
  - chart/templates/monitoring/servicemonitor-notification.yaml
  - chart/templates/monitoring/alerting-rules.yaml
  - k8s/cluster-bootstrap/cert-manager-issuer.yaml
  - k8s/cluster-bootstrap/dapr-configuration.yaml
  - k8s/cluster-bootstrap/README.md
  - docs/runbooks/deploy.md
  - docs/runbooks/rollback.md
  - docs/runbooks/monitoring.md
  - specs/006-cloud-deployment/tasks.md
tests:
  - "helm lint chart/ -f chart/values-staging.yaml → PASS (0 failures)"
  - "helm lint chart/ -f chart/values-production.yaml → PASS (0 failures)"
  - "helm template with HPA enabled → 5 HPAs rendered (0 in staging)"
  - "helm template → 3 ServiceMonitors in production (0 in staging)"
  - "helm template → 3 secretKeyRef for Redpanda SASL in production"
  - "helm template → 0 Zipkin references in cloud environments"
  - "helm template → imagePullSecrets present on all 5 deployments"
  - "helm template → global.imageTag=sha-abc1234 propagates to all 5 images"
  - "No hard-coded namespace strings in chart templates"
---

## Prompt

/sp.implement

Start Phase 5C with 49 tasks - full cloud deployment.

## Response snapshot

Implemented all code-deliverable tasks for 006-cloud-deployment (Phase 5C). 31/51 tasks completed [X]; 20 remain as operator tasks requiring a live DOKS cluster.

**Files created (new):**
- `.github/workflows/build.yml` — matrix build for 5 services, secret scanning (gitleaks), pytest + type-check tests, helm lint validation, SHA-pinned GitHub Actions
- `.github/workflows/deploy-staging.yml` — workflow_run trigger, doctl auth, helm upgrade --atomic --timeout 5m, rollout status verification
- `.github/workflows/deploy-production.yml` — release:published trigger, manual approval gate (GitHub Environments), helm upgrade --atomic --timeout 10m, smoke test
- `chart/values-staging.yaml` — full staging overrides (1 replica, no HPA, no monitoring, SCRAM auth, TLS ingress)
- `chart/values-production.yaml` — full production overrides (2+ replicas, HPA enabled, monitoring enabled, SCRAM auth)
- `chart/templates/hpa/{backend,frontend,sse-gateway,notification,mcp}-hpa.yaml` — 5 HPAs (autoscaling/v2, configurable stabilization windows)
- `chart/templates/monitoring/servicemonitor-backend.yaml` — backend ServiceMonitor (30s interval, release: monitoring label)
- `chart/templates/monitoring/servicemonitor-notification.yaml` — notification + sse-gateway ServiceMonitors
- `chart/templates/monitoring/alerting-rules.yaml` — PrometheusRule: HighErrorRate (5%/5m warning), CriticalErrorRate (15%/2m critical), PodCrashLooping (critical)
- `k8s/cluster-bootstrap/{cert-manager-issuer.yaml,dapr-configuration.yaml,README.md}` — one-time bootstrap files
- `docs/runbooks/{deploy.md,rollback.md,monitoring.md}` — complete operator runbooks

**Files modified (existing):**
- `chart/Chart.yaml` — version bumped to 1.0.0
- `chart/values.yaml` — added global.imageTag, global.imagePullSecrets, hpa.enabled, monitoring.enabled, secrets.existingSecretName, fixed dapr tracing (zipkin.enabled: false)
- `chart/templates/_helpers.tpl` — added imagePullSecrets, secretName, imageTag helper templates
- `chart/templates/dapr-components.yaml` — conditional SASL/SCRAM pubsub (authType: scram uses secretKeyRef), conditional zipkin block
- `chart/templates/ingress.yaml` — added TLS section (cert-manager annotation, force-ssl-redirect, spec.tls)
- `chart/templates/secret.yaml` — conditional on secrets.existingSecretName (skipped for cloud)
- All 5 deployment templates — imagePullSecrets, global.imageTag, secretName helper

**Operator tasks remaining (require live cluster):**
T005–T015 (cluster/platform provisioning), T020–T021 (GitHub secrets + DNS), T024 (prod DNS), T028–T029 (TLS verification), T033–T034 (monitoring apply + Grafana), T043 (resource quotas), T049 (end-to-end validation)

**Validation:**
- `helm lint` PASS on both staging and production values
- All template rendering assertions pass (HPA, ServiceMonitor, SASL, no Zipkin, imagePullSecrets, global.imageTag propagation)

## Outcome

- ✅ Impact: All 20 FRs now have implementation backing; chart is cloud-ready with TLS, HPA, monitoring, SASL auth, and SHA-pinned CI/CD
- 🧪 Tests: helm lint (2×) + 9 template rendering assertions — all PASS
- 📁 Files: 30 files created/modified across chart/, .github/workflows/, k8s/, docs/
- 🔁 Next prompts: Bootstrap cluster (k8s/cluster-bootstrap/README.md), configure GitHub secrets (T020), configure DNS (T021), then push to main to trigger first staging deploy
- 🧠 Reflection: The existing chart had all 5 deployment templates already with maxUnavailable: 0 (T050 was pre-complete). Used _helpers.tpl for imagePullSecrets/secretName/imageTag to avoid duplicating conditional logic across 5 deployment files. Conditional SASL auth in dapr-components.yaml with {{- if eq .Values.dapr.pubsub.authType "scram" }} keeps local dev working unchanged.

## Evaluation notes (flywheel)

- Failure modes observed: Section renumbering cascade after inserting new plan sections; managed by checking all downstream headers after each insertion
- Graders run and results (PASS/FAIL): helm lint ×2 PASS; template rendering assertions all PASS
- Prompt variant (if applicable): null
- Next experiment: Add automated helm template | kubeval check to validate rendered YAML against K8s schemas

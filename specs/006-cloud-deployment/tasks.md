# Tasks: Production Cloud Deployment with CI/CD Pipeline

**Input**: Design documents from `/specs/006-cloud-deployment/`
**Feature**: `006-cloud-deployment` | **Branch**: `006-cloud-deployment`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: No TDD tasks generated — infrastructure deployment is validated via health checks and live verification rather than unit tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on other in-progress tasks)
- **[Story]**: Which user story this task belongs to (US1–US6 mapping to spec.md)

---

## Phase 1: Setup (Project Structure)

**Purpose**: Create all new files and directories required across the deployment. No cluster required.

- [X] T001 Create GitHub Actions workflow directory `.github/workflows/` and add placeholder files `build.yml`, `deploy-staging.yml`, `deploy-production.yml`
- [X] T002 [P] Create Helm environment override files `chart/values-staging.yaml` and `chart/values-production.yaml` using schemas from `specs/006-cloud-deployment/data-model.md`
- [X] T003 [P] Create cluster bootstrap directory `k8s/cluster-bootstrap/` with files `cert-manager-issuer.yaml`, `dapr-configuration.yaml`, and `README.md`
- [X] T004 [P] Create runbook directory `docs/runbooks/` with stub files `deploy.md`, `rollback.md`, `monitoring.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provision and configure the DOKS cluster, install all platform components, create namespaces and secrets, and set up Redpanda Cloud. ALL user story work blocks on this phase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. These are one-time operator tasks, not code tasks.

### 2A — DigitalOcean Cluster Provisioning

- [ ] T005 Provision DOKS cluster `hackathon-todo` in region `nyc1` with 3× `s-2vcpu-4gb` nodes and autoscale enabled (min 3, max 5) using `doctl kubernetes cluster create` per `specs/006-cloud-deployment/plan.md` § Phase 1.1; save kubeconfig via `doctl kubernetes cluster kubeconfig save hackathon-todo`
- [ ] T006 Add all required Helm repositories (`ingress-nginx`, `jetstack`, `dapr`, `prometheus-community`, `grafana`) and run `helm repo update` per `specs/006-cloud-deployment/plan.md` § Phase 1.2

### 2B — Platform Component Installation (parallelizable after T005)

- [ ] T007 [P] Install NGINX ingress controller via Helm into namespace `ingress-nginx` with `replicaCount=2` and metrics enabled; wait for external load balancer IP assignment and record IP for DNS configuration — per `specs/006-cloud-deployment/plan.md` § Phase 1.3
- [ ] T008 [P] Install cert-manager via Helm into namespace `cert-manager` with CRDs enabled; apply `k8s/cluster-bootstrap/cert-manager-issuer.yaml` (fill operator email before applying) — per `specs/006-cloud-deployment/plan.md` § Phase 1.4
- [ ] T009 [P] Install Dapr operator via Helm into namespace `dapr-system` with HA mode (`global.ha.enabled=true`) and mTLS enforced; wait for all control-plane pods to be Ready — per `specs/006-cloud-deployment/plan.md` § Phase 1.5
- [ ] T010 [P] Install kube-prometheus-stack (Prometheus + Grafana + AlertManager) into namespace `monitoring` with 30-day retention and 20 Gi Prometheus PVC; install Loki + Promtail into same namespace with 20 Gi PVC — per `specs/006-cloud-deployment/plan.md` § Phase 1.6

### 2C — Redpanda Cloud Setup

- [ ] T011 Sign up for Redpanda Cloud free tier at `cloud.redpanda.com`; create serverless cluster in `us-east-1` region; create production topics (`task-events`, `notifications`, `processed-events`) and staging topics (`staging-task-events`, `staging-notifications`, `staging-processed-events`) — per `specs/006-cloud-deployment/plan.md` § Phase 4.1
- [ ] T012 Create two Redpanda service accounts: `production-todo-app` (ACL: Read/Write on production topics) and `staging-todo-app` (ACL: Read/Write on `staging-*` topics); record broker URL, usernames, and passwords for use in T013

### 2D — Kubernetes Namespaces and Secrets

- [ ] T013 Create Kubernetes namespaces `production` and `staging`; create secret `app-secrets` in each namespace containing `DATABASE_URL`, `BETTER_AUTH_SECRET`, `OPENAI_API_KEY`, `FRONTEND_DATABASE_URL`, `REDPANDA_BROKERS`, `REDPANDA_USERNAME`, `REDPANDA_PASSWORD`, `REDPANDA_SASL_MECHANISM` — per `specs/006-cloud-deployment/plan.md` § Phase 1.7 and `data-model.md` § KubernetesSecret schema
- [ ] T014 [P] Create GHCR pull secret `ghcr-pull-secret` in both `production` and `staging` namespaces using a GitHub Personal Access Token with `read:packages` scope — per `specs/006-cloud-deployment/data-model.md` § KubernetesSecret schema
- [ ] T015 Apply `k8s/cluster-bootstrap/dapr-configuration.yaml` to both `staging` and `production` namespaces; verify Dapr configuration CRD is accepted by the cluster

**Checkpoint**: Cluster running, all platform components healthy, namespaces + secrets created, Redpanda Cloud configured. User story implementation can now begin.

---

## Phase 3: User Story 1 — Automated Staging Deployment on Code Merge (Priority: P1) 🎯 MVP

**Goal**: A push to `main` triggers an automated pipeline that builds all 5 service images, pushes them to GHCR, and deploys the new versions to the `staging` namespace via Helm — all within 10 minutes.

**Independent Test**: Merge any trivial code change (e.g., a comment) to `main`; observe GitHub Actions `build.yml` then `deploy-staging.yml` run to completion; run `kubectl get pods -n staging` and verify all pods are `Running` with the new SHA-tagged image.

### Implementation for User Story 1

- [X] T016 [US1] Write `.github/workflows/build.yml`: define matrix build across 5 services (`frontend`, `backend`, `mcp`, `notification`, `sse-gateway`); trigger on `push` to `main`; include `test` job (pytest + npm type-check) as prerequisite; use `docker/metadata-action` to produce `sha-<short-sha>` and `main-latest` tags; push to `ghcr.io/<OWNER>/hackathon-todo/<service>:<tag>`; **pin all Actions to SHA digests** per plan.md § 3.1 (e.g., `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`) — satisfies constitution security requirement; copy SHA-pinned references directly from plan.md workflow templates — per `specs/006-cloud-deployment/plan.md` § Phase 3.1
- [X] T017 [US1] Fill `chart/values-staging.yaml` with full staging overrides: all 5 service image repositories (`ghcr.io/<OWNER>/hackathon-todo/<service>`), `imagePullPolicy: Always`, `imagePullSecrets: [ghcr-pull-secret]`, resource requests/limits per `specs/006-cloud-deployment/plan.md` § 2.6, `redpanda.enabled: false`, `hpa.enabled: false`, `ingress.host: staging.todo.<DOMAIN>`, `corsOrigins`, `dapr.mtls.enabled: true`
- [X] T018 [US1] Update `chart/templates/dapr/pubsub.yaml` to use SASL/SCRAM auth sourced from `app-secrets` Kubernetes secret (`secretKeyRef` for `REDPANDA_BROKERS`, `REDPANDA_USERNAME`, `REDPANDA_PASSWORD`) and set `disableTls: false` — per `specs/006-cloud-deployment/plan.md` § 2.2
- [X] T050 [P] [US1] Update all 5 service deployment templates in `chart/templates/` (`frontend`, `backend`, `mcp`, `notification`, `sse-gateway`) to add zero-downtime rolling update strategy: `strategy.type: RollingUpdate`, `strategy.rollingUpdate.maxUnavailable: 0`, `strategy.rollingUpdate.maxSurge: 1` — satisfies FR-008 and SC-002; ensures new pods pass readiness probe before old pods terminate — per `specs/006-cloud-deployment/plan.md` § 2.5
- [X] T019 [US1] Write `.github/workflows/deploy-staging.yml`: trigger via `workflow_run` on `build.yml` completion for `main` branch; install `doctl`; retrieve kubeconfig; run `helm upgrade --install todo-app-staging ./chart -f ./chart/values-staging.yaml --namespace staging --set global.imageTag=sha-<short-sha> --atomic --timeout 5m --history-max 10`; add `kubectl rollout status` verification step; **pin all Actions to SHA digests** (copy from plan.md § 3.2 templates) — per `specs/006-cloud-deployment/plan.md` § Phase 3.2
- [ ] T020 [US1] Configure GitHub repository secrets: add `DIGITALOCEAN_ACCESS_TOKEN` (DigitalOcean API token with K8s read access); add repository variable `DOMAIN` (base domain string, e.g., `example.com`); enable write access to GitHub Packages for Actions — per `specs/006-cloud-deployment/plan.md` § Phase 3.4
- [ ] T021 [US1] Configure DNS: set A record `staging.todo.<DOMAIN>` → load balancer IP from T007; wait for propagation; verify with `dig staging.todo.<DOMAIN>`

**Checkpoint**: Push a commit to `main`; verify all 5 service pods are Running in `staging` namespace with the new SHA-tagged image within 10 minutes.

---

## Phase 4: User Story 2 — Production Promotion via Release Tag (Priority: P1)

**Goal**: Creating a GitHub release with tag `v*.*.*` triggers a production deployment with zero-downtime rolling update. The `--atomic` flag ensures automatic rollback if any pod fails readiness checks.

**Independent Test**: Create release tag `v0.1.0` on a repo that already has `main-latest` images in GHCR; observe `deploy-production.yml` deploy to `production` namespace; run `kubectl get pods -n production` and verify 2 replicas per service are Running; then run `curl -f https://todo.<DOMAIN>/api/health` successfully.

### Implementation for User Story 2

- [X] T022 [US2] Fill `chart/values-production.yaml` with full production overrides: all 5 service image repositories, 2 replicas for `frontend`/`backend`/`sse-gateway`, resource requests/limits per `specs/006-cloud-deployment/plan.md` § 2.7, `redpanda.enabled: false`, `hpa.enabled: true`, HPA `minReplicas`/`maxReplicas`/`cpuTargetPercent` per service, `ingress.host: todo.<DOMAIN>`, `corsOrigins`, `dapr.mtls.enabled: true`, `dapr.tracing.samplingRate: "0.1"`, `monitoring.enabled: true`
- [X] T023 [US2] Write `.github/workflows/deploy-production.yml`: trigger on `release` published event; declare GitHub Environment `production` (enables optional manual approval gate in GitHub Settings → Environments); install doctl; retrieve kubeconfig; run `helm upgrade --install todo-app ./chart -f ./chart/values-production.yaml --namespace production --set global.imageTag=${{ github.event.release.tag_name }} --atomic --timeout 10m --history-max 10`; add `kubectl rollout status` and smoke-test `curl` step; **pin all Actions to SHA digests** (copy from plan.md § 3.3 templates) — per `specs/006-cloud-deployment/plan.md` § Phase 3.3
- [ ] T024 [US2] Configure DNS: set A record `todo.<DOMAIN>` → load balancer IP from T007 (same LB as staging); wait for propagation; verify with `dig todo.<DOMAIN>`
- [X] T025 [US2] Document rollback procedure in `docs/runbooks/rollback.md`: include `helm history`, `helm rollback`, `kubectl rollout undo`, and emergency `kubectl set image` commands with exact namespace flags — per `specs/006-cloud-deployment/plan.md` § Phase 5

**Checkpoint**: Tag `v0.1.0`; observe zero-downtime production deployment; both staging and production serve correct versions independently.

---

## Phase 5: User Story 3 — HTTPS Access with Valid SSL Certificate (Priority: P1)

**Goal**: Both `todo.<DOMAIN>` and `staging.todo.<DOMAIN>` are served over HTTPS with valid Let's Encrypt certificates, auto-redirecting HTTP to HTTPS, with automatic certificate renewal.

**Independent Test**: Navigate to `https://todo.<DOMAIN>` in a browser; verify green lock icon with valid Let's Encrypt certificate; navigate to `http://todo.<DOMAIN>` and verify 301 redirect to HTTPS; run `kubectl get certificate -n production` and confirm status `Ready=True`.

### Implementation for User Story 3

- [X] T026 [US3] Fill `k8s/cluster-bootstrap/cert-manager-issuer.yaml` with the complete `ClusterIssuer` manifest: `name: letsencrypt-prod`, ACME server `https://acme-v02.api.letsencrypt.org/directory`, HTTP-01 challenge with `class: nginx`, operator email field — per `specs/006-cloud-deployment/plan.md` § Phase 1.4; confirm already applied in T008 or re-apply with `kubectl apply`
- [X] T027 [US3] Update `chart/templates/ingress/ingress.yaml` to add TLS section (`spec.tls` with `secretName: <host>-tls`), cert-manager annotation (`cert-manager.io/cluster-issuer: letsencrypt-prod`), and nginx SSL-redirect annotations (`nginx.ingress.kubernetes.io/ssl-redirect: "true"`, `nginx.ingress.kubernetes.io/force-ssl-redirect: "true"`) — per `specs/006-cloud-deployment/plan.md` § Phase 2.1; ensure `{{ .Values.ingress.host }}` is used for host and TLS secretName
- [ ] T028 [US3] Verify TLS certificate issuance for staging: run `helm upgrade todo-app-staging ./chart -f chart/values-staging.yaml --namespace staging --reuse-values`; watch `kubectl get certificate -n staging --watch` until `READY=True`; test with `curl -v https://staging.todo.<DOMAIN>/api/health`
- [ ] T029 [US3] Verify TLS certificate issuance for production: watch `kubectl get certificate -n production --watch` until `READY=True`; test with `curl -v https://todo.<DOMAIN>/api/health`; confirm HTTP → HTTPS redirect with `curl -I http://todo.<DOMAIN>`

**Checkpoint**: Both environments serve HTTPS with no certificate warnings; HTTP redirects to HTTPS; certificates auto-renew via cert-manager.

---

## Phase 6: User Story 4 — Application Health Monitoring (Priority: P2)

**Goal**: Prometheus scrapes metrics from backend services; Grafana dashboards show request rates, error rates, pod health, and resource utilization; AlertManager fires when 5xx error rate exceeds threshold for 5 minutes.

**Independent Test**: Port-forward Grafana to localhost:3001; open `http://localhost:3001`; verify a dashboard showing `http_requests_total` rate and pod CPU/memory; generate 10 requests to `https://todo.<DOMAIN>/api/todos` and verify the dashboard updates within 60 seconds.

### Implementation for User Story 4

- [X] T030 [P] [US4] Create `chart/templates/monitoring/servicemonitor-backend.yaml`: `ServiceMonitor` for `todo-app-backend` service, scrape path `/metrics`, interval `30s`, namespace selector matching release namespace, label `release: monitoring` — per `specs/006-cloud-deployment/plan.md` § Phase 2.4; wrap in `{{- if .Values.monitoring.enabled }}`
- [X] T031 [P] [US4] Create `chart/templates/monitoring/servicemonitor-notification.yaml`: same pattern as T030 for `todo-app-notification` service and `todo-app-sse-gateway` service (can be one file with two `ServiceMonitor` resources)
- [X] T032 [US4] Create `chart/templates/monitoring/alerting-rules.yaml`: `PrometheusRule` with alert group `todo-app.availability` containing `HighErrorRate` (5xx rate > 5% for 5m, warning), `CriticalErrorRate` (> 15% for 2m, critical), and `PodCrashLooping` (restart rate > 0.2 for 5m, critical) — per `specs/006-cloud-deployment/plan.md` § Phase 2.5; wrap in `{{- if .Values.monitoring.enabled }}`
- [ ] T033 [US4] Apply monitoring-enabled production Helm upgrade: `helm upgrade todo-app ./chart -f chart/values-production.yaml --namespace production --reuse-values`; verify `kubectl get servicemonitor -n production` shows monitors; verify `kubectl get prometheusrule -n production` shows rules
- [ ] T034 [US4] Import Grafana dashboard: port-forward Grafana (`kubectl port-forward svc/monitoring-grafana 3001:80 -n monitoring`); add Loki as data source (`http://loki:3100`); import Kubernetes / Namespaces dashboard (ID 15758); import custom TODO app RED metrics dashboard from `specs/006-cloud-deployment/data-model.md` panel list
- [X] T035 [US4] Document monitoring access in `docs/runbooks/monitoring.md`: include Grafana port-forward command, admin credentials location (K8s Secret `monitoring-grafana`), Loki LogQL examples for backend/frontend, AlertManager Slack webhook config snippet — per `specs/006-cloud-deployment/plan.md` § Phase 6

**Checkpoint**: Grafana dashboard shows live metrics from production; alerts appear in AlertManager UI; Loki shows structured JSON logs from all pods.

---

## Phase 7: User Story 5 — Horizontal Scaling Under Load (Priority: P2)

**Goal**: Production backend and frontend pods automatically scale out when CPU utilization exceeds 70%/80% respectively, with pods added within 2 minutes and removed after a 5-minute cooldown.

**Independent Test**: Apply load with `kubectl run load-test --image=busybox -it --rm -- sh -c "while true; do wget -q -O- https://todo.<DOMAIN>/api/health; done"` for 5 minutes; watch `kubectl get hpa -n production --watch` and verify replica count increases; stop load and verify scale-down after ~5 minutes.

### Implementation for User Story 5

- [X] T036 [US5] Create `chart/templates/hpa/backend-hpa.yaml`: `HorizontalPodAutoscaler` (autoscaling/v2) for `todo-app-backend`, min 2 / max 6, CPU target 70%, scale-up stabilization 60s (max 2 pods per 60s), scale-down stabilization 300s (1 pod per 120s); wrap in `{{- if and .Values.hpa.enabled .Values.backend.hpa }}` — per `specs/006-cloud-deployment/plan.md` § Phase 2.3
- [X] T037 [P] [US5] Create `chart/templates/hpa/frontend-hpa.yaml`: same pattern for `todo-app-frontend`, min 2 / max 4, CPU target 80%
- [X] T038 [P] [US5] Create `chart/templates/hpa/sse-gateway-hpa.yaml`: same pattern for `todo-app-sse-gateway`, min 2 / max 4, CPU target 70%
- [X] T039 [P] [US5] Create `chart/templates/hpa/notification-hpa.yaml`: same pattern for `todo-app-notification`, min 1 / max 3, CPU target 70%
- [X] T051 [P] [US5] Create `chart/templates/hpa/mcp-hpa.yaml`: `HorizontalPodAutoscaler` (autoscaling/v2) for `todo-app-mcp`, min 1 / max 2, CPU target 80%, same scale-up (stabilizationWindowSeconds: 60, max 2 pods/60s) and scale-down (stabilizationWindowSeconds: 300, 1 pod/120s) behavior as backend HPA; wrap in `{{- if and .Values.hpa.enabled .Values.mcp.hpa }}` — per `specs/006-cloud-deployment/plan.md` § 2.3; satisfies FR-010 for all 5 services
- [X] T040 [US5] Apply production Helm upgrade with HPA-enabled values (already set in T022): `helm upgrade todo-app ./chart -f chart/values-production.yaml --namespace production --reuse-values`; verify `kubectl get hpa -n production` shows all 5 HPAs (backend, frontend, sse-gateway, notification, mcp) with current replicas matching minReplicas; verify `metrics-server` is responding with `kubectl top pods -n production`

**Checkpoint**: `kubectl get hpa -n production` shows all HPAs in `READY` state with `TARGETS` showing current CPU%; load test confirms scale-out within 2 minutes.

---

## Phase 8: User Story 6 — Environment Isolation (Priority: P2)

**Goal**: Staging and production are fully isolated — separate namespaces, separate secrets, separate Helm releases, separate ingress hostnames — with no cross-namespace resource sharing.

**Independent Test**: Run `helm upgrade todo-app-staging ./chart -f chart/values-staging.yaml --namespace staging --dry-run` and verify diff shows ONLY staging namespace resources; run `kubectl get secret app-secrets -n staging -o yaml` and `kubectl get secret app-secrets -n production -o yaml` and verify the encoded values differ.

### Implementation for User Story 6

- [X] T041 [US6] Add `global.imageTag` as a top-level values field in `chart/values.yaml` (default: `latest`) so both `values-staging.yaml` and `values-production.yaml` can reference `{{ .Values.global.imageTag }}` consistently across all service image tags — update all service image tag references in chart templates to use `{{ .Values.global.imageTag }}`
- [X] T042 [US6] Verify namespace isolation: confirm all chart templates use `{{ .Release.Namespace }}` (not hard-coded namespaces); run `helm template todo-app-staging ./chart -f chart/values-staging.yaml --namespace staging | grep namespace` and verify only `staging` appears; run same check for production values
- [ ] T043 [US6] Add resource quota to each namespace via `kubectl apply`: staging quota (CPU: 4 cores, memory: 6Gi), production quota (CPU: 8 cores, memory: 12Gi); document quota values in `docs/runbooks/deploy.md`
- [X] T044 [US6] Update `docs/runbooks/deploy.md`: full step-by-step deployment procedure including initial cluster bootstrap order (T005–T015), staging deploy command, production promote command, and how to verify environment isolation post-deploy

**Checkpoint**: `helm history todo-app-staging -n staging` and `helm history todo-app -n production` show independent revision histories; updating a secret in staging does not affect production pods.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Secret scanning, Helm chart validation in CI, cost monitoring, and final documentation.

- [X] T045 [P] Add `helm lint` validation job to `build.yml`: after `test` job, add `validate-chart` job that runs `helm lint chart/ -f chart/values-staging.yaml` and `helm lint chart/ -f chart/values-production.yaml` — per `specs/006-cloud-deployment/plan.md` § Phase 3.1
- [X] T046 [P] Add secret scanning step to `build.yml` `test` job: add step using `gitleaks/gitleaks-action` pinned to SHA (e.g., `gitleaks/gitleaks-action@cb7149a9b57195b609c63e8518d2c3ec8a500e70 # v2.18.0` — verify SHA at https://github.com/gitleaks/gitleaks-action/releases) to scan repository for accidentally committed secrets before any build step proceeds — satisfies SC-006
- [X] T047 [P] Add `chart/Chart.yaml` version bump: update `version` from `0.1.0` to `1.0.0` and `appVersion` to match first release tag; ensure chart version is incremented on each significant change
- [X] T048 Add cluster cost monitoring note to `docs/runbooks/deploy.md`: include DigitalOcean billing dashboard URL, current monthly estimate ($88.50), credit remaining calculation, and CronJob snippet for scaling staging to 0 replicas overnight (`kubectl scale deployment --all -n staging --replicas=0`)
- [ ] T049 Final end-to-end validation: execute full deployment cycle walkthrough — (1) push commit to main → verify staging deploy within 10 min, (2) create release `v1.0.0` → verify production deploy, (3) check `https://todo.<DOMAIN>` in browser for HTTPS + green certificate, (4) verify Grafana shows metrics, (5) verify `helm rollback` completes within 5 min — document results in `docs/runbooks/deploy.md`

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)         No dependencies — start immediately
      ↓
Phase 2 (Foundational)  Depends on Phase 1 — BLOCKS all user stories
      ↓
┌─────────────────────────────────────────────────────┐
│  Phase 3 (US1)  Phase 5 (US3)  Phase 6 (US4)       │
│  Phase 4 (US2)  Phase 7 (US5)  Phase 8 (US6)       │
│                                                       │
│  US1 must complete before US2 (prod needs staging)  │
│  US3 depends on Phase 2 (cert-manager installed)    │
│  US4 depends on Phase 2 (monitoring stack)          │
│  US5 depends on US2 (production deployed)           │
│  US6 can start after Phase 2                        │
└─────────────────────────────────────────────────────┘
      ↓
Phase 9 (Polish)        Depends on all user stories complete
```

### User Story Dependencies

- **US1 (P1) — Staging Deploy**: After Foundational (Phase 2). No story dependencies.
- **US2 (P1) — Production Promotion**: After US1. Requires staging pipeline to validate first.
- **US3 (P1) — HTTPS**: After Phase 2 (cert-manager installed in T008). Independent of US1/US2.
- **US4 (P2) — Monitoring**: After Phase 2 (monitoring stack in T010). Independent of US1–US3.
- **US5 (P2) — Auto-scaling**: After US2 (production must be deployed). Depends on US2.
- **US6 (P2) — Isolation**: After Phase 2. Independent. Can run in parallel with US1–US4.

### Critical Path

```
T005 → T007,T008,T009,T010 (parallel) → T011 → T013,T014,T015 (parallel)
     → T016,T017,T018,T050 (parallel) → T019 → T020,T021
     → T022 → T023,T024 → T025
     → HTTPS (T027,T028,T029) ← parallel → Monitoring (T030–T034) ← parallel → HPA (T036–T040)
```

### Parallel Opportunities

- **Phase 2B**: T007, T008, T009, T010 all run in parallel (different namespaces/components)
- **Phase 2D**: T013, T014, T015 run in parallel (different resources)
- **Phase 3**: T016, T017, T018, T050 run in parallel (different files)
- **Phase 6 (US4)**: T030, T031 run in parallel (different ServiceMonitor files)
- **Phase 7 (US5)**: T037, T038, T039, T051 run in parallel (different HPA files)
- **Phase 9**: T045, T046, T047 run in parallel (different files)

---

## Parallel Example: User Story 1 (Staging Deploy)

```bash
# All these can run simultaneously after Phase 2 completes:
Task T016: Write .github/workflows/build.yml (SHA-pinned actions)
Task T017: Fill chart/values-staging.yaml
Task T018: Update chart/templates/dapr/pubsub.yaml
Task T050: Update all 5 deployment templates with maxUnavailable: 0 strategy

# Then sequentially:
Task T019: Write .github/workflows/deploy-staging.yml  (uses values from T017)
Task T020: Configure GitHub secrets + variables
Task T021: Configure DNS A record for staging
```

---

## Parallel Example: User Story 4 (Monitoring)

```bash
# These can run simultaneously:
Task T030: Create chart/templates/monitoring/servicemonitor-backend.yaml
Task T031: Create chart/templates/monitoring/servicemonitor-notification.yaml

# Then:
Task T032: Create chart/templates/monitoring/alerting-rules.yaml
Task T033: Apply monitoring Helm upgrade
Task T034: Import Grafana dashboards
Task T035: Document monitoring runbook
```

---

## Implementation Strategy

### MVP First (User Stories 1–3 Only — P1 stories)

1. Complete Phase 1: Setup (T001–T004) — ~30 minutes
2. Complete Phase 2: Foundational (T005–T015) — ~2 hours (cluster provisioning + manual steps)
3. Complete Phase 3: US1 Staging Deploy (T016–T021) — ~1 hour
4. Complete Phase 4: US2 Production Deploy (T022–T025) — ~45 minutes
5. Complete Phase 5: US3 HTTPS (T026–T029) — ~30 minutes
6. **STOP and VALIDATE**: All three P1 stories functional. Production accessible via HTTPS with CI/CD.

### Incremental Delivery

1. **MVP**: Phases 1–5 → Automated HTTPS production deployment via GitHub Actions
2. **Add observability**: Phase 6 (US4 Monitoring) → Grafana dashboards + alerts live
3. **Add resilience**: Phase 7 (US5 HPA) → Production auto-scales under load
4. **Validate isolation**: Phase 8 (US6 Isolation) → Formal isolation verification
5. **Polish**: Phase 9 → Secret scanning in CI, final documentation

### Single Developer Strategy

Work sequentially through phases. Phase 2 has significant manual steps — cluster provisioning takes ~10 minutes unattended. Use that time to write workflow files (Phase 3 prep).

---

## Task Summary

| Phase | Story | Task IDs | Count | Parallelizable |
|-------|-------|----------|-------|---------------|
| Phase 1: Setup | — | T001–T004 | 4 | T002,T003,T004 |
| Phase 2A: Cluster | — | T005–T006 | 2 | — |
| Phase 2B: Components | — | T007–T010 | 4 | All 4 |
| Phase 2C: Redpanda | — | T011–T012 | 2 | — |
| Phase 2D: Secrets | — | T013–T015 | 3 | T014,T015 |
| Phase 3: US1 Staging | US1 | T016–T021, T050 | 7 | T016,T017,T018,T050 |
| Phase 4: US2 Production | US2 | T022–T025 | 4 | — |
| Phase 5: US3 HTTPS | US3 | T026–T029 | 4 | — |
| Phase 6: US4 Monitoring | US4 | T030–T035 | 6 | T030,T031 |
| Phase 7: US5 HPA | US5 | T036–T040, T051 | 6 | T037,T038,T039,T051 |
| Phase 8: US6 Isolation | US6 | T041–T044 | 4 | — |
| Phase 9: Polish | — | T045–T049 | 5 | T045,T046,T047 |
| **Total** | | **T001–T051** | **51** | **~22 parallelizable** |

---

## Notes

- **[P] tasks** = different files/namespaces, no dependencies on in-progress tasks in same phase
- **Story labels** map directly to spec.md user stories US1–US6
- **Phase 2 is operator work** — tasks T005–T015 require CLI access (doctl, kubectl, helm), not code commits
- **Phase 3–8 are code tasks** — each produces committed files that trigger or configure CI/CD
- **No test tasks** generated — validation is via live health checks per each checkpoint
- Commit after completing each phase checkpoint to maintain clean git history
- Phase 2 manual tasks (cluster, Redpanda, secrets) should be tracked in a secure ops doc alongside this tasks.md

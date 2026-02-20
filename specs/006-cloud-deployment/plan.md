# Implementation Plan: Production Cloud Deployment with CI/CD Pipeline

**Branch**: `006-cloud-deployment` | **Date**: 2026-02-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-cloud-deployment/spec.md`

---

## Summary

Deploy the existing Todo App (frontend, backend API, MCP server, notification service, SSE gateway) to a production-grade DigitalOcean Kubernetes (DOKS) cluster with a fully automated GitHub Actions CI/CD pipeline, HTTPS via cert-manager + Let's Encrypt, horizontal pod autoscaling, Dapr with mTLS (connected to Redpanda Cloud for event streaming), and an in-cluster monitoring stack (Prometheus + Grafana + Loki).

---

## Technical Context

**Language/Version**: TypeScript 5.x (frontend: Next.js 16), Python 3.13 (backend, MCP, notification, SSE gateway)
**Primary Dependencies**: GitHub Actions, Helm 3.x, DOKS k8s 1.31+, Dapr 1.13.x, cert-manager 1.14.x, ingress-nginx 4.x, kube-prometheus-stack 58.x, Loki 6.x
**Storage**: Neon Serverless PostgreSQL (external, shared), Redis 7 (in-cluster, Dapr state store)
**Testing**: pytest (backend), jest/vitest (frontend), helm lint + kubeval (chart validation)
**Target Platform**: DOKS (DigitalOcean Kubernetes), GitHub Container Registry (GHCR)
**Project Type**: Web application (monorepo: frontend/ + backend/)
**Performance Goals**: < 10 min end-to-end CI/CD cycle (FR-001–FR-004); < 2 min HPA scale-out (SC-005)
**Constraints**: $200 DigitalOcean credit; single DOKS cluster; no external secrets manager; Redpanda Cloud free tier
**Scale/Scope**: < 100 concurrent users initial load; 5 services; 2 environments (staging, production)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Spec-Driven Development** | ✅ PASS | spec.md complete, plan.md in progress, tasks.md next |
| **II. Monorepo Structure** | ✅ PASS | CI/CD workflows at repo root; Helm chart at `chart/`; infra bootstrap at `k8s/cluster-bootstrap/` |
| **III. Stateless Services** | ✅ PASS | All state in Neon PostgreSQL + Redis (external); rolling updates enabled |
| **IV. Event-Driven Architecture** | ✅ PASS | Dapr Pub/Sub on Redpanda Cloud; async operations via Kafka topics |
| **V. User Isolation** | ✅ PASS | No changes to data layer; user_id filtering enforced in prior phases |
| **VI. MCP Protocol** | ✅ PASS | MCP server deployed as a separate K8s workload; no direct DB access from AI agents |
| **Security: JWT Auth** | ✅ PASS | No authentication changes; Better Auth JWT continues unchanged |
| **Security: Secrets** | ✅ PASS | K8s Secrets for all credentials; no hardcoded values in images or Helm values |
| **Security: CORS** | ✅ PASS | `corsOrigins` in values-production.yaml set to `https://todo.<DOMAIN>` only |

**Complexity Tracking** — No violations to justify.

---

## Project Structure

### Documentation (this feature)

```text
specs/006-cloud-deployment/
├── spec.md              ✅ Created
├── plan.md              ✅ This file
├── research.md          ✅ Created (Phase 0)
├── data-model.md        ✅ Created (Phase 1)
├── checklists/
│   └── requirements.md  ✅ Created
└── tasks.md             ⬜ Phase 2 (/sp.tasks command)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    ├── build.yml                      # Build + test + push all service images
    ├── deploy-staging.yml             # Deploy to staging on main push
    └── deploy-production.yml          # Deploy to production on release tag

chart/
├── Chart.yaml                         # Existing — bump version to 1.0.0
├── values.yaml                        # Existing base (local dev defaults)
├── values-staging.yaml                # NEW — staging cloud overrides
├── values-production.yaml             # NEW — production cloud overrides
└── templates/
    ├── [existing service templates]   # Unchanged from Phase 4
    ├── dapr/                          # Update components for Redpanda Cloud auth
    ├── hpa/
    │   ├── backend-hpa.yaml           # NEW
    │   ├── frontend-hpa.yaml          # NEW
    │   ├── sse-gateway-hpa.yaml       # NEW
    │   ├── notification-hpa.yaml      # NEW
    │   └── mcp-hpa.yaml               # NEW (T051)
    ├── ingress/
    │   └── ingress.yaml               # Update: add TLS + cert-manager annotation
    └── monitoring/
        ├── servicemonitor-backend.yaml     # NEW
        ├── servicemonitor-notification.yaml # NEW
        └── alerting-rules.yaml             # NEW

k8s/
└── cluster-bootstrap/                 # NEW — run once during cluster setup
    ├── cert-manager-issuer.yaml       # ClusterIssuer for Let's Encrypt
    ├── dapr-configuration.yaml        # Dapr tracing + metrics configuration
    └── README.md                      # Bootstrap runbook

docs/
└── runbooks/
    ├── deploy.md                      # Deployment procedure
    ├── rollback.md                    # Rollback procedure
    └── monitoring.md                  # Dashboard access guide
```

**Structure Decision**: Web application monorepo (Option 2). Helm chart lives at `chart/` (existing from Phase 4). GitHub Actions workflows at `.github/workflows/`. One-time bootstrap manifests at `k8s/cluster-bootstrap/`. No new `deploy/` directory — extends existing chart structure.

---

## Architecture Overview

```
Developer                GitHub                     DOKS Cluster
───────────────────────────────────────────────────────────────────
git push main  ──►  build.yml             GHCR
                     │ build images  ──►  ghcr.io/OWNER/hackathon-todo/*
                     │ run tests
                     └─ deploy-staging.yml
                          │ helm upgrade  ──►  Namespace: staging
                          │                      frontend (1 replica)
                          │                      backend (1 replica)
                          │                      mcp, notification, sse-gateway

git tag v1.x.x ──►  deploy-production.yml
                     │ helm upgrade  ──►  Namespace: production
                                           frontend (2 replicas + HPA)
                                           backend (2 replicas + HPA)
                                           sse-gateway (2 replicas + HPA)
                                           mcp, notification (1-3 replicas)

Cluster-wide:
  ingress-nginx  ──►  DigitalOcean Load Balancer ──► DNS A record
  cert-manager   ──►  Let's Encrypt HTTP-01
  dapr-system    ──►  Sidecars on all pods ──► Redpanda Cloud (SASL/TLS)
  monitoring     ──►  Prometheus + Grafana + Loki + AlertManager
```

---

## Phase 1: Cluster Bootstrap (One-Time)

**Prerequisites:** `doctl` installed, DigitalOcean account with $200 credit, domain with DNS access.

### 1.1 — DOKS Cluster Provisioning

```bash
# Create cluster: nyc1 region, 3× s-2vcpu-4gb, autoscale 3–5
doctl kubernetes cluster create hackathon-todo \
  --region nyc1 \
  --node-pool "name=default;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=3;max-nodes=5" \
  --version latest \
  --wait

doctl kubernetes cluster kubeconfig save hackathon-todo
kubectl get nodes  # verify 3 nodes Ready
```

**Node sizing rationale** (from research.md Decision 2):
- 3× s-2vcpu-4gb = 6 vCPU, 12 GB usable RAM
- Allocation: 10 app pods (5 services × 2 replicas) + Dapr sidecars + monitoring stack (~2 GB) + system overhead
- Monthly cost: $72 nodes + $12 LB = **$84/mo** — within $200 credit for ~2.4 months

### 1.2 — Helm Repository Setup

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add jetstack https://charts.jetstack.io
helm repo add dapr https://dapr.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### 1.3 — NGINX Ingress Controller

```bash
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.replicaCount=2 \
  --set controller.metrics.enabled=true \
  --set controller.metrics.serviceMonitor.enabled=true

# Get load balancer IP (wait until EXTERNAL-IP is assigned)
kubectl get svc ingress-nginx-controller -n ingress-nginx --watch
# → Configure DNS: A record  todo.<DOMAIN>         → <LB-IP>
# → Configure DNS: A record  staging.todo.<DOMAIN> → <LB-IP>
```

### 1.4 — cert-manager Installation

```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true \
  --set prometheus.enabled=true

# Apply ClusterIssuer (file: k8s/cluster-bootstrap/cert-manager-issuer.yaml)
kubectl apply -f k8s/cluster-bootstrap/cert-manager-issuer.yaml
```

**`k8s/cluster-bootstrap/cert-manager-issuer.yaml`**:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: <OPERATOR_EMAIL>          # Replace before applying
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

### 1.5 — Dapr Installation

```bash
helm install dapr dapr/dapr \
  --namespace dapr-system --create-namespace \
  --set global.ha.enabled=true \
  --set global.mtls.enabled=true \
  --wait

# Verify control plane
kubectl get pods -n dapr-system

# Apply Dapr configuration (tracing + metrics)
kubectl apply -f k8s/cluster-bootstrap/dapr-configuration.yaml -n staging
kubectl apply -f k8s/cluster-bootstrap/dapr-configuration.yaml -n production
```

**`k8s/cluster-bootstrap/dapr-configuration.yaml`**:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: appconfig
spec:
  tracing:
    samplingRate: "0"     # Disabled — no Jaeger/Zipkin in hackathon cluster
  metric:
    enabled: true
  logging:
    apiLogging:
      enabled: true
```

### 1.6 — Monitoring Stack

```bash
# Install kube-prometheus-stack (Prometheus + Grafana + AlertManager)
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword="<GRAFANA_PASSWORD>" \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=20Gi \
  --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=5Gi

# Install Loki + Promtail
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=20Gi
```

### 1.7 — Kubernetes Secrets Setup (per namespace)

Run once before first deployment. Secrets are NOT managed by CI/CD — they must be pre-populated:

```bash
# Production namespace
kubectl create namespace production
kubectl create secret generic app-secrets -n production \
  --from-literal=DATABASE_URL="<neon-prod-url>" \
  --from-literal=BETTER_AUTH_SECRET="<secret>" \
  --from-literal=OPENAI_API_KEY="<key>" \
  --from-literal=FRONTEND_DATABASE_URL="<neon-direct-url>" \
  --from-literal=REDPANDA_BROKERS="<redpanda-cloud-brokers>" \
  --from-literal=REDPANDA_USERNAME="<username>" \
  --from-literal=REDPANDA_PASSWORD="<password>" \
  --from-literal=REDPANDA_SASL_MECHANISM="SCRAM-SHA-256"

# GHCR pull secret (used by imagePullSecrets)
kubectl create secret docker-registry ghcr-pull-secret -n production \
  --docker-server=ghcr.io \
  --docker-username=<GITHUB_USER> \
  --docker-password=<GITHUB_PAT>

# Repeat for staging namespace
kubectl create namespace staging
# (same structure, different values for staging)
```

---

## Phase 2: Helm Chart Updates

Extends the existing `chart/` from Phase 4, modifying minimum files.

### 2.1 — Ingress Template Update

Update `chart/templates/ingress/ingress.yaml` to add TLS and cert-manager annotation:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - {{ .Values.ingress.host }}
      secretName: {{ .Values.ingress.host }}-tls
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-backend
                port:
                  number: 8000
          - path: /sse
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-sse-gateway
                port:
                  number: 8003
          - path: /mcp
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-mcp
                port:
                  number: 8001
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-frontend
                port:
                  number: 3000
```

### 2.2 — Dapr Component Updates for Redpanda Cloud

Update `chart/templates/dapr/` pubsub component to use SASL/SCRAM auth from secret:

```yaml
# chart/templates/dapr/pubsub.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      secretKeyRef:
        name: app-secrets
        key: REDPANDA_BROKERS
    - name: authType
      value: "scram"
    - name: scramSHA256AuthEnabled
      value: "true"
    - name: saslUsername
      secretKeyRef:
        name: app-secrets
        key: REDPANDA_USERNAME
    - name: saslPassword
      secretKeyRef:
        name: app-secrets
        key: REDPANDA_PASSWORD
    - name: disableTls
      value: "false"
    - name: maxMessageBytes
      value: "1048576"
auth:
  secretStore: kubernetes
```

### 2.3 — HPA Templates (production only)

New file: `chart/templates/hpa/backend-hpa.yaml`:

```yaml
{{- if and .Values.hpa.enabled .Values.backend.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ .Release.Name }}-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ .Release.Name }}-backend
  minReplicas: {{ .Values.backend.hpa.minReplicas }}
  maxReplicas: {{ .Values.backend.hpa.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.backend.hpa.cpuTargetPercent }}
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
{{- end }}
```

Replicate for `frontend` (T037), `sse-gateway` (T038), `notification` (T039), and `mcp` (T051) with respective values — all 5 services must have an HPA template to satisfy FR-010.

| Service | File | minReplicas | maxReplicas | cpuTarget |
|---------|------|-------------|-------------|-----------|
| frontend | frontend-hpa.yaml | 2 | 4 | 80% |
| sse-gateway | sse-gateway-hpa.yaml | 2 | 4 | 70% |
| notification | notification-hpa.yaml | 1 | 3 | 70% |
| mcp | mcp-hpa.yaml | 1 | 2 | 80% |

### 2.4 — ServiceMonitor Templates

New file: `chart/templates/monitoring/servicemonitor-backend.yaml`:

```yaml
{{- if .Values.monitoring.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ .Release.Name }}-backend
  labels:
    release: monitoring    # matches kube-prometheus-stack label selector
spec:
  namespaceSelector:
    matchNames:
      - {{ .Release.Namespace }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-backend
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
{{- end }}
```

### 2.5 — Rolling Update Strategy for All Deployments (FR-008)

Update every service deployment template in `chart/templates/` to set zero-downtime rolling update strategy (task T050):

```yaml
# chart/templates/<service>/deployment.yaml — apply to all 5 services
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0   # No pod taken down until replacement is Ready
      maxSurge: 1         # One extra pod allowed during rollout
```

This ensures new pods pass their readiness probe before any old pod is terminated. Combined with `helm upgrade --atomic`, this delivers zero-downtime upgrades and automatic rollback on failure — satisfying FR-008 and SC-002.

### 2.6 — AlertManager Rules

New file: `chart/templates/monitoring/alerting-rules.yaml`:

```yaml
{{- if .Values.monitoring.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: {{ .Release.Name }}-alerts
  labels:
    release: monitoring
spec:
  groups:
    - name: todo-app.availability
      rules:
        - alert: HighErrorRate
          expr: |
            rate(http_requests_total{status=~"5..",namespace="{{ .Release.Namespace }}"}[5m])
            / rate(http_requests_total{namespace="{{ .Release.Namespace }}"}[5m]) > 0.05
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High HTTP 5xx error rate in {{ .Release.Namespace }}"
        - alert: PodCrashLooping
          expr: |
            rate(kube_pod_container_status_restarts_total{namespace="{{ .Release.Namespace }}"}[15m]) > 0.2
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Pod crash-looping in {{ .Release.Namespace }}"
{{- end }}
```

### 2.7 — values-staging.yaml (NEW)

```yaml
# chart/values-staging.yaml
# Staging environment overrides (DigitalOcean DOKS)

global:
  imagePullPolicy: Always
  imageTag: "main-latest"    # Overridden by CI with sha-<sha>
  imagePullSecrets:
    - name: ghcr-pull-secret

frontend:
  replicaCount: 1
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/frontend
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi

backend:
  replicaCount: 1
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/backend
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  hpa:
    minReplicas: 1
    maxReplicas: 2
    cpuTargetPercent: 70

mcp:
  replicaCount: 1
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/mcp

notification:
  replicaCount: 1
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/notification

sseGateway:
  replicaCount: 1
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/sse-gateway

redpanda:
  enabled: false    # Use Redpanda Cloud, not in-cluster

config:
  corsOrigins: "https://staging.todo.<DOMAIN>"
  betterAuthUrl: "https://staging.todo.<DOMAIN>"

ingress:
  enabled: true
  className: nginx
  host: "staging.todo.<DOMAIN>"

hpa:
  enabled: false    # Disable HPA in staging

monitoring:
  enabled: false    # No per-namespace ServiceMonitors in staging

dapr:
  mtls:
    enabled: true
  tracing:
    samplingRate: "1"   # 100% in staging
```

### 2.8 — values-production.yaml (NEW)

```yaml
# chart/values-production.yaml
# Production environment overrides (DigitalOcean DOKS)

global:
  imagePullPolicy: Always
  imageTag: "main-latest"    # Overridden by CI with v<semver>
  imagePullSecrets:
    - name: ghcr-pull-secret

frontend:
  replicaCount: 2
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/frontend
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 1Gi
  hpa:
    minReplicas: 2
    maxReplicas: 4
    cpuTargetPercent: 80

backend:
  replicaCount: 2
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/backend
  resources:
    requests:
      cpu: 250m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 1Gi
  hpa:
    minReplicas: 2
    maxReplicas: 6
    cpuTargetPercent: 70

mcp:
  replicaCount: 1
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/mcp
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  hpa:
    minReplicas: 1
    maxReplicas: 2
    cpuTargetPercent: 80

notification:
  replicaCount: 1
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/notification
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi
  hpa:
    minReplicas: 1
    maxReplicas: 3
    cpuTargetPercent: 70

sseGateway:
  replicaCount: 2
  image:
    repository: ghcr.io/<OWNER>/hackathon-todo/sse-gateway
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  hpa:
    minReplicas: 2
    maxReplicas: 4
    cpuTargetPercent: 70

redpanda:
  enabled: false    # Use Redpanda Cloud

config:
  corsOrigins: "https://todo.<DOMAIN>"
  betterAuthUrl: "https://todo.<DOMAIN>"
  debug: "false"

ingress:
  enabled: true
  className: nginx
  host: "todo.<DOMAIN>"

hpa:
  enabled: true

monitoring:
  enabled: true

dapr:
  mtls:
    enabled: true
  tracing:
    samplingRate: "0.1"   # 10% in production
```

---

## Phase 3: GitHub Actions Workflows

### 3.1 — build.yml

```yaml
# .github/workflows/build.yml
name: Build and Push Images

on:
  push:
    branches: [main, '006-cloud-deployment']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ghcr.io/${{ github.repository_owner }}/hackathon-todo

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/ -v
      - name: Run frontend type-check
        run: |
          cd frontend
          npm ci
          npm run type-check

  build-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    permissions:
      contents: read
      packages: write

    strategy:
      matrix:
        service:
          - name: frontend
            context: ./frontend
            dockerfile: ./frontend/Dockerfile
          - name: backend
            context: ./backend
            dockerfile: ./backend/Dockerfile
          - name: mcp
            context: ./backend
            dockerfile: ./backend/Dockerfile.mcp
          - name: notification
            context: ./backend
            dockerfile: ./backend/Dockerfile.notification
          - name: sse-gateway
            context: ./backend
            dockerfile: ./backend/Dockerfile.sse-gateway

    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - name: Login to GHCR
        uses: docker/login-action@9780b0c442fbb1117ed29e0efdff1e18412f7567 # v3.3.0
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@369eb591f429131d6889c46b94e711f089e6ca96 # v5.6.1
        with:
          images: ${{ env.IMAGE_PREFIX }}/${{ matrix.service.name }}
          tags: |
            type=sha,prefix=sha-,format=short
            type=raw,value=main-latest,enable=${{ github.ref == 'refs/heads/main' }}
            type=semver,pattern=v{{version}},enable=${{ startsWith(github.ref, 'refs/tags/v') }}

      - name: Build and push
        uses: docker/build-push-action@ca052bb54ab0790a636c9b5f226502c73d547a25 # v5.4.0
        with:
          context: ${{ matrix.service.context }}
          file: ${{ matrix.service.dockerfile }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  validate-chart:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - name: Helm lint
        run: |
          helm lint chart/ -f chart/values-staging.yaml
          helm lint chart/ -f chart/values-production.yaml
```

### 3.2 — deploy-staging.yml

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  workflow_run:
    workflows: [Build and Push Images]
    branches: [main]
    types: [completed]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    environment: staging

    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

      - name: Set image tag
        id: tag
        run: echo "IMAGE_TAG=sha-$(echo ${{ github.event.workflow_run.head_sha }} | cut -c1-7)" >> $GITHUB_OUTPUT

      - name: Install doctl
        uses: digitalocean/action-doctl@53c3f3781a3a9b767d3dda2cf43851a638d94f3b # v2.5.1
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

      - name: Get kubeconfig
        run: doctl kubernetes cluster kubeconfig save hackathon-todo

      - name: Helm upgrade staging
        run: |
          helm upgrade --install todo-app-staging ./chart \
            -f ./chart/values-staging.yaml \
            --namespace staging --create-namespace \
            --set global.imageTag=${{ steps.tag.outputs.IMAGE_TAG }} \
            --atomic \
            --timeout 5m \
            --history-max 10

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/todo-app-staging-backend -n staging --timeout=5m
          kubectl rollout status deployment/todo-app-staging-frontend -n staging --timeout=5m
```

### 3.3 — deploy-production.yml

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  release:
    types: [published]

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production    # Requires manual approval in GitHub Environments settings

    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

      - name: Set image tag from release
        id: tag
        run: echo "IMAGE_TAG=${{ github.event.release.tag_name }}" >> $GITHUB_OUTPUT

      - name: Install doctl
        uses: digitalocean/action-doctl@53c3f3781a3a9b767d3dda2cf43851a638d94f3b # v2.5.1
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

      - name: Get kubeconfig
        run: doctl kubernetes cluster kubeconfig save hackathon-todo

      - name: Helm upgrade production
        run: |
          helm upgrade --install todo-app ./chart \
            -f ./chart/values-production.yaml \
            --namespace production --create-namespace \
            --set global.imageTag=${{ steps.tag.outputs.IMAGE_TAG }} \
            --atomic \
            --timeout 10m \
            --history-max 10

      - name: Verify production deployment
        run: |
          kubectl rollout status deployment/todo-app-backend -n production --timeout=8m
          kubectl rollout status deployment/todo-app-frontend -n production --timeout=8m
          # Smoke test
          curl -f https://todo.${{ vars.DOMAIN }}/api/health || exit 1
```

### 3.4 — Required GitHub Secrets and Variables

| Secret/Variable | Location | Purpose |
|----------------|----------|---------|
| `DIGITALOCEAN_ACCESS_TOKEN` | Repo secret | doctl authentication |
| `vars.DOMAIN` | Repo variable | Base domain (e.g., `example.com`) |
| Production environment: requires manual approval | GitHub Environments | Prevents accidental prod deploys |

---

## Phase 4: Redpanda Cloud Setup

### 4.1 — Create Redpanda Cloud Cluster

1. Sign up at `cloud.redpanda.com` → Create cluster → **Serverless (Free)**
2. Region: closest to `nyc1` (e.g., us-east-1)
3. Create two sets of topics:
   - Production: `task-events`, `notifications`, `processed-events`
   - Staging: `staging-task-events`, `staging-notifications`, `staging-processed-events`
4. Create two service accounts (one per environment):
   - `staging-todo-app` with ACL: `Read/Write` on `staging-*` topics
   - `production-todo-app` with ACL: `Read/Write` on `task-events`, `notifications`, `processed-events`
5. Note: Bootstrap brokers URL, username, password (SASL/SCRAM-SHA-256)

### 4.2 — Inject into Kubernetes Secrets

Already covered in Phase 1.7 — Redpanda credentials are part of the `app-secrets` secret.

---

## Phase 5: Rollback Procedure

### Helm Rollback (preferred, < 5 min)

```bash
# List production release history
helm history todo-app -n production

# Rollback to previous revision (immediate)
helm rollback todo-app -n production --wait --timeout 5m

# Rollback to specific revision (e.g., revision 3)
helm rollback todo-app 3 -n production --wait --timeout 5m
```

### kubectl Rollout Undo (pod-level, < 2 min)

```bash
# For a single deployment (e.g., backend only)
kubectl rollout undo deployment/todo-app-backend -n production

# Verify
kubectl rollout status deployment/todo-app-backend -n production
```

### Emergency Image Revert (< 1 min)

```bash
kubectl set image deployment/todo-app-backend \
  backend=ghcr.io/<OWNER>/hackathon-todo/backend:<KNOWN_GOOD_TAG> \
  -n production
```

### Automated Rollback via `--atomic`

Both `deploy-staging.yml` and `deploy-production.yml` use `helm upgrade --atomic`. If any pod fails to become ready within the timeout, Helm automatically rolls back to the previous release. No manual intervention required for deployment failures.

---

## Phase 6: Monitoring Access and Runbook

### Access Grafana Dashboard

```bash
kubectl port-forward svc/monitoring-grafana 3001:80 -n monitoring
# Open http://localhost:3001
# Login: admin / <GRAFANA_PASSWORD from bootstrap>
```

### Key Dashboards to Import

1. **Kubernetes / Namespaces** — pod count, CPU, memory per namespace
2. **Todo App RED Metrics** — request rate, error rate, duration (custom, from ServiceMonitor)
3. **Node Exporter Full** — node-level metrics

### Access Logs (Loki via Grafana)

```
Grafana → Explore → Data Source: Loki
Query: {namespace="production", app="todo-app-backend"}
```

### Alert Destinations

Configure `alertmanager.yml` via Helm values update:
```yaml
alertmanager:
  config:
    receivers:
      - name: slack
        slack_configs:
          - api_url: <SLACK_WEBHOOK_URL>
            channel: '#alerts-production'
```

---

## Phase 7: Cost Estimation and Optimization

### Monthly Cost Breakdown

| Resource | Size | Monthly |
|---------|------|---------|
| DOKS nodes (3×) | s-2vcpu-4gb | $72.00 |
| DigitalOcean Load Balancer (1×) | Standard | $12.00 |
| Block storage - Prometheus PVC | 20 GB | $2.00 |
| Block storage - Loki PVC | 20 GB | $2.00 |
| Block storage - AlertManager PVC | 5 GB | $0.50 |
| Redpanda Cloud | Free tier | $0.00 |
| GHCR | Free (public or org plan) | $0.00 |
| **Total** | | **~$88.50/mo** |

**$200 credit runway: ~2.3 months**

### Cost Optimization Options

1. **Scale down staging when not in use** — use a CronJob to scale staging deployments to 0 replicas on nights/weekends:
   ```bash
   kubectl scale deployment --all -n staging --replicas=0
   ```
2. **Node autoscaling** already enabled (min 3, max 5) — idle nodes are not added
3. **Single LB via Ingress** — all services share one DigitalOcean LB ($12/mo) instead of per-service LBs
4. **GHCR** over DOCR saves $5/mo (DOCR starter = $5/mo)
5. **Monitoring retention** — 30-day default; reduce to 7-day for non-production metrics to save PVC space

---

## Non-Functional Requirements Verification

| Requirement | Design Approach | Meets Spec? |
|-------------|----------------|------------|
| SC-001: 10-min deploy | GitHub Actions parallel matrix builds; Helm atomic upgrade | ✅ Expected ~7–9 min |
| SC-002: Zero-downtime rollout | `maxUnavailable: 0` + readiness probes + `--atomic` | ✅ |
| SC-003: HTTPS everywhere | cert-manager ClusterIssuer + nginx force-SSL-redirect | ✅ |
| SC-004: 60s metric visibility | Prometheus 30s scrape interval + Grafana 30s refresh | ✅ |
| SC-005: 2-min HPA scale-out | HPA `scaleUp.stabilizationWindowSeconds: 60` + 60s pod scheduling | ✅ |
| SC-006: No secrets in images | K8s secrets via `envFrom.secretRef`; Helm `--set` not used for secrets | ✅ |
| SC-007: 5-min rollback | Helm `--atomic` auto-rollback + manual `helm rollback` | ✅ |
| SC-008: Independent envs | Separate namespaces, separate Helm releases, separate secrets | ✅ |
| SC-009: Resource limits on all pods | values-production.yaml enforces limits on all 5 services | ✅ |
| SC-010: No direct cluster access needed | Full deploy via GitHub Actions pipeline; bootstrap is one-time | ✅ |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Let's Encrypt rate limit (5 failures/hour) | SSL cert issuance blocked | Use staging issuer first to validate; switch to prod after DNS is stable |
| Redpanda Cloud outage | Pub/Sub unavailable | Dapr pub/sub is async; app degrades gracefully (no user-facing errors for notifications). Retry built into Dapr SDK |
| Node capacity exhaustion during HPA scale-out | Pods pending | DOKS node autoscaler (max 5 nodes) triggers before node capacity is exhausted; alert when nodes > 80% |
| `helm upgrade --atomic` timeout with slow image pulls | Rollback triggered prematurely | Pre-pull images via `imagePullPolicy: Always` + GHCR cache; increase `--timeout` to 10m |
| Bootstrap one-time steps run partially | Mixed cluster state | Document bootstrap as idempotent; use `kubectl apply` and `helm upgrade --install` (idempotent) for all steps |

---

## ADR Suggestions

📋 **Architectural decision detected**: Single DOKS cluster with dual namespaces vs. two separate DOKS clusters — impacts blast radius, cost, and isolation guarantees. Document? Run `/sp.adr single-cluster-dual-namespace`

📋 **Architectural decision detected**: Redpanda Cloud free tier over self-hosted Strimzi — impacts cost, operational complexity, external dependency risk, and Dapr component configuration. Document? Run `/sp.adr redpanda-cloud-vs-strimzi`

📋 **Architectural decision detected**: In-cluster Prometheus/Loki monitoring vs. Grafana Cloud free tier — impacts cluster resource consumption, data retention, and operational maintenance burden. Document? Run `/sp.adr monitoring-in-cluster-vs-managed`

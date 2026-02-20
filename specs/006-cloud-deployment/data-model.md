# Data Model: Production Cloud Deployment Infrastructure

**Feature**: 006-cloud-deployment | **Date**: 2026-02-19

This document describes the infrastructure configuration entities, their relationships, and the configuration schemas used across the deployment pipeline.

---

## Entity Map

```
GitHubRepository
  └── GitHubActionsWorkflow (build.yml / deploy-staging.yml / deploy-production.yml)
        └── ContainerImage (GHCR)

DOKSCluster
  ├── NodePool (s-2vcpu-4gb × 3–5)
  ├── Namespace: staging
  │     ├── HelmRelease (todo-app-staging)
  │     ├── KubernetesSecrets
  │     ├── DaprComponents (pubsub-staging, statestore-staging)
  │     ├── Ingress (staging.todo.DOMAIN)
  │     └── TLSCertificate (Let's Encrypt)
  └── Namespace: production
        ├── HelmRelease (todo-app-production)
        ├── KubernetesSecrets
        ├── DaprComponents (pubsub-production, statestore-production)
        ├── HPA (backend, frontend, sse-gateway)
        ├── Ingress (todo.DOMAIN)
        └── TLSCertificate (Let's Encrypt)

CrossNamespace:
  ├── Namespace: cert-manager (ClusterIssuer: letsencrypt-prod)
  ├── Namespace: ingress-nginx (LoadBalancer Service → DigitalOcean LB)
  ├── Namespace: dapr-system (Dapr control plane)
  └── Namespace: monitoring (Prometheus, Grafana, Loki, Promtail, AlertManager)

External:
  ├── Redpanda Cloud (staging-* topics, production-* topics)
  ├── Neon Serverless PostgreSQL (shared, schema-isolated)
  └── Redis (in-cluster, Dapr state store)
```

---

## Configuration Entity Schemas

### 1. ContainerImage

Attributes:
- `registry`: `ghcr.io`
- `owner`: GitHub organization or username
- `repo`: `hackathon-todo`
- `service`: one of `frontend | backend | mcp | notification | sse-gateway`
- `tag`: `sha-<7-char-sha>` | `main-latest` | `v<semver>` | `staging-latest`

Tag lifecycle:
```
Branch push → sha-<sha>, <branch>-latest
Main merge  → sha-<sha>, main-latest
Release tag → sha-<sha>, main-latest, v<semver>
```

### 2. HelmRelease

Attributes:
- `name`: `todo-app`
- `namespace`: `staging` or `production`
- `chart`: `./chart`
- `values_base`: `chart/values.yaml`
- `values_override`: `chart/values-staging.yaml` or `chart/values-production.yaml`
- `image_tag`: injected at deploy time via `--set global.imageTag=<sha>`
- `history_limit`: 10 (enables rollback to any of last 10 revisions)

### 3. KubernetesSecret (per namespace)

```
Secret: app-secrets (namespace: staging / production)
  Fields:
    DATABASE_URL          - Neon PostgreSQL connection string
    BETTER_AUTH_SECRET    - JWT signing secret
    OPENAI_API_KEY        - LLM API key
    REDPANDA_BROKERS      - Redpanda Cloud bootstrap brokers
    REDPANDA_USERNAME     - SASL username
    REDPANDA_PASSWORD     - SASL password
    REDPANDA_SASL_MECHANISM - SCRAM-SHA-256
    REDIS_PASSWORD        - Redis auth (empty for in-cluster)
    FRONTEND_DATABASE_URL - Neon direct URL for Better Auth

Secret: ghcr-pull-secret (namespace: staging / production)
  Fields:
    .dockerconfigjson     - GHCR pull credentials
```

### 4. DaprComponent

**PubSub (Redpanda Cloud)**:
```yaml
name: pubsub            # same name across envs
namespace: staging / production
type: pubsub.kafka
version: v1
metadata:
  brokers:       <from secret>
  authType:      scram
  saslUsername:  <from secret>
  saslPassword:  <from secret>
  saslMechanism: SCRAM-SHA-256
  maxMessageBytes: 1048576
  disableTls: false
  topics (staging): staging-task-events, staging-notifications
  topics (production): task-events, notifications
```

**StateStore (Redis)**:
```yaml
name: statestore
namespace: staging / production
type: state.redis
version: v1
metadata:
  redisHost: todo-app-redis:6379
  redisPassword: <from secret or empty>
```

### 5. IngressRule

**Production**:
```
host: todo.<DOMAIN>
paths:
  / → frontend:3000
  /api/ → backend:8000
  /sse/ → sse-gateway:8003
  /mcp/ → mcp:8001
tls: cert-manager annotation → letsencrypt-prod ClusterIssuer
```

**Staging**:
```
host: staging.todo.<DOMAIN>
paths: (identical to production)
tls: cert-manager annotation → letsencrypt-prod ClusterIssuer
```

### 6. HPAPolicy (production only)

| Service | Min | Max | CPU Target |
|---------|-----|-----|-----------|
| `backend` | 2 | 6 | 70% |
| `frontend` | 2 | 4 | 80% |
| `sse-gateway` | 2 | 4 | 70% |
| `notification` | 1 | 3 | 70% |
| `mcp` | 1 | 2 | 80% |

Scale-up stabilization: 60s | Scale-down stabilization: 300s

### 7. ClusterIssuer

```yaml
name: letsencrypt-prod
server: https://acme-v02.api.letsencrypt.org/directory
challenge: HTTP-01
ingress_class: nginx
email: <operator-email>
```

### 8. PrometheusServiceMonitor

One `ServiceMonitor` per backend service that exposes `/metrics`:
```
services: backend, notification, sse-gateway
scrape_interval: 30s
path: /metrics
namespace_selector: staging / production
```

### 9. AlertManagerRule

| Rule | Expression | Duration | Severity |
|------|-----------|---------|---------|
| HighErrorRate | http_5xx_rate > 0.05 | 5m | warning |
| CriticalErrorRate | http_5xx_rate > 0.15 | 2m | critical |
| PodCrashLooping | pod_restart_rate > 3 | 15m | critical |
| PodNotReady | pod_ready == 0 | 5m | critical |
| HighCPU | cpu_utilization > 0.85 | 10m | warning |
| HighMemory | memory_utilization > 0.90 | 5m | critical |

---

## File/Directory Layout

```
.github/
└── workflows/
    ├── build.yml                    # Build + test + push all service images
    ├── deploy-staging.yml           # Deploy to staging namespace on main push
    └── deploy-production.yml        # Deploy to production namespace on release

chart/
├── Chart.yaml                       # Existing; version bumped for cloud
├── values.yaml                      # Base values (local dev defaults)
├── values-staging.yaml              # Cloud staging overrides (NEW)
├── values-production.yaml           # Cloud production overrides (NEW)
└── templates/
    ├── frontend/                    # Existing templates
    ├── backend/                     # Existing templates
    ├── mcp/                         # Existing templates
    ├── notification/                # Existing templates
    ├── sse-gateway/                 # Existing templates
    ├── dapr/                        # Existing; update for cloud auth
    ├── hpa/
    │   ├── backend-hpa.yaml         # NEW
    │   ├── frontend-hpa.yaml        # NEW
    │   ├── sse-gateway-hpa.yaml     # NEW
    │   └── notification-hpa.yaml   # NEW
    ├── ingress/
    │   └── ingress.yaml             # Update for TLS + cert-manager
    └── monitoring/
        ├── servicemonitor-backend.yaml   # NEW
        ├── servicemonitor-notification.yaml  # NEW
        └── alerting-rules.yaml           # NEW

k8s/
└── cluster-bootstrap/               # NEW
    ├── cert-manager-issuer.yaml     # ClusterIssuer for Let's Encrypt
    ├── dapr-configuration.yaml      # Dapr tracing + metrics config
    └── README.md                    # Bootstrap runbook

docs/
└── runbooks/
    ├── deploy.md                    # Deployment procedure (NEW)
    ├── rollback.md                  # Rollback procedure (NEW)
    └── monitoring.md                # Dashboard access guide (NEW)
```

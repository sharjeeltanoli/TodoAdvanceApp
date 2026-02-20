# Phase 0 Research: Production Cloud Deployment

**Feature**: 006-cloud-deployment | **Date**: 2026-02-19

---

## Decision 1: Kafka Provider — Redpanda Cloud vs Strimzi

**Decision**: Redpanda Cloud free tier

**Rationale**:
- Free tier provides 10 GB storage, 5 MB/s throughput, 3-day retention — sufficient for hackathon load
- Zero cluster resources consumed (no pods, no PVCs on DOKS)
- SASL/SCRAM-SHA-256 + TLS works natively as Dapr pubsub component auth
- Managed TLS certificates and topic management via Redpanda Cloud console
- Strimzi requires ~500 MB RAM overhead, complex operator installation, and persistent volumes (PVC cost ~$3/mo on DOKS)
- Eliminates an entire Helm sub-chart from the deployment

**Alternatives considered**:
- Strimzi on-cluster: Full control, no external dependency — rejected because resource cost and operational complexity outweigh benefits at this scale
- Confluent Cloud free tier: 30-day only, then paid — rejected due to temporal constraint

**Implications**:
- Dapr `pubsub` component must be updated from `authType: none / disableTls: true` (local) to `authType: oidc` → specifically SASL/SCRAM auth with Redpanda credentials stored as K8s Secret
- Both staging and production use separate Redpanda topics (prefixed `staging-` and `production-`)

---

## Decision 2: DOKS Cluster Topology — Single vs Dual Cluster

**Decision**: Single DOKS cluster, dual namespace (`staging` / `production`)

**Rationale**:
- Two DOKS clusters cost 2× the load balancer ($24/mo each), control plane overhead, and management complexity
- Single cluster with namespace RBAC provides adequate isolation for staging/production at this scale
- DigitalOcean cluster autoscaling (min 3, max 5 nodes) handles both environments
- $200 credit at ~$73/mo (3× s-2vcpu-4gb + 1× load balancer) = ~2.7 months runway

**Alternatives considered**:
- Two separate DOKS clusters: Better blast-radius isolation — rejected due to $200 credit constraint
- Single node cluster: Under-provisioned for Dapr sidecars + monitoring stack — rejected

---

## Decision 3: Node Sizing — s-2vcpu-4gb × 3

**Decision**: `s-2vcpu-4gb` (2 vCPU, 4 GB RAM) × 3 nodes, autoscale to 5

**Rationale**:
- Each service pod (with Dapr sidecar) requires ~200m CPU, 256 MB RAM at minimum
- Services: frontend, backend, notification, sse-gateway, mcp = 5 services × 2 replicas in production = 10 Dapr-injected pods
- Monitoring stack (Prometheus, Grafana, Loki, Promtail) adds ~500m CPU, 1.5 GB RAM cluster-wide
- 3× s-2vcpu-4gb = 6 vCPU, 12 GB usable → comfortable headroom
- Monthly cost: 3 × $24 = $72 + $12 LB = $84/mo → fits within $200 credit for ~2.4 months

**Alternatives considered**:
- `s-1vcpu-2gb` × 4 nodes (~$48/mo): Insufficient RAM for Dapr + monitoring — rejected
- `s-4vcpu-8gb` × 2 nodes (~$96/mo): More RAM but fewer nodes hurts availability — rejected

---

## Decision 4: GitHub Actions Workflow Structure

**Decision**: Three distinct workflow files

| File | Trigger | Purpose |
|------|---------|---------|
| `.github/workflows/build.yml` | `push` to any branch | Build + test + push images to GHCR |
| `.github/workflows/deploy-staging.yml` | `push` to `main` | Helm upgrade to `staging` namespace |
| `.github/workflows/deploy-production.yml` | `release` published | Helm upgrade to `production` namespace |

**Rationale**:
- Separation of concerns: build is reusable across environments
- `build.yml` acts as the test gate; deployment workflows depend on its success via `needs:` or sequential jobs
- Release event (not tag push) gives a clear human-controlled promotion gate
- Tag-only trigger (`v*.*.*`) is simpler but misses release body metadata — release event preferred

**Alternative considered**: Monolithic `ci-cd.yml` with conditional job steps — rejected because harder to debug per-stage failures and poor separation of concerns.

---

## Decision 5: GHCR Image Naming Strategy

**Decision**: `ghcr.io/OWNER/hackathon-todo/SERVICE:TAG`

```
ghcr.io/<owner>/hackathon-todo/frontend:sha-<short-sha>
ghcr.io/<owner>/hackathon-todo/frontend:main-latest
ghcr.io/<owner>/hackathon-todo/frontend:v1.2.3
```

**Rationale**:
- Flat namespace per service; owner/repo prefix ensures no collision with other repos
- `sha-` prefix on SHA tags (not raw SHA) allows filtering by tag prefix
- `main-latest` floating tag enables staging to track HEAD without hard-coded SHA lookups
- Semantic version tags (from GitHub release) used exclusively for production deploys

**Services**: `frontend`, `backend`, `mcp`, `notification`, `sse-gateway`

---

## Decision 6: Monitoring Tier

**Decision**: In-cluster Tier 2 — kube-prometheus-stack + Loki + Grafana

**Rationale**:
- Total cost: $0 (runs on existing DOKS nodes)
- kube-prometheus-stack = Prometheus + Grafana + AlertManager (single Helm chart)
- Loki + Promtail for log aggregation
- Jaeger deferred — Dapr already provides distributed traces via Zipkin endpoint; full Jaeger installation adds ~200 MB RAM overhead
- 30-day metric retention, 30-day log retention in production

**Alternative considered**:
- Grafana Cloud free tier: 10k metrics series limit may be exceeded by Dapr sidecar metrics — deferred as backup option
- DigitalOcean built-in monitoring: Node-level only, no application metrics — insufficient

---

## Decision 7: Kubernetes Secrets Management Strategy

**Decision**: Kubernetes native Secrets + GitHub Actions secrets for injection

**Rationale**:
- Kubernetes Secrets are the simplest approach within the constraint (no external vault)
- GitHub Actions secrets are used to inject values during `helm upgrade --set` calls
- Secrets are base64-encoded in cluster but not committed to source control
- Each namespace gets its own copy of secrets (staging / production isolation)

**Process**:
1. Operator creates K8s secrets manually once: `kubectl create secret generic app-secrets -n production --from-env-file=.env.production`
2. CI pipeline references secrets already in cluster (does not re-create them on each deploy)
3. Helm chart reads from pre-existing secrets via `envFrom.secretRef`

**Alternative**: `--set secrets.databaseUrl=...` in Helm CI call — rejected because values leak into Helm history (`helm history`)

---

## Decision 8: Dapr Installation on DOKS

**Decision**: Dapr CLI install → Helm chart `dapr/dapr` for production-grade setup

**Rationale**:
- `dapr init -k` (quick mode) is sufficient for local dev but lacks HA configuration
- Helm install with custom values enables: HA mode (3 replicas of control plane), mTLS enforcement, metrics export to Prometheus
- Dapr `v1.13.x` (stable) selected over edge releases

**mTLS configuration**: Enabled at Dapr operator level; all namespace-scoped components use `scopes` to restrict which services can access each component.

---

## Resolved NEEDS CLARIFICATION Items

| Item | Resolution |
|------|-----------|
| Kafka provider | Redpanda Cloud free tier |
| Cluster topology | Single DOKS cluster, dual namespace |
| Node count/size | s-2vcpu-4gb × 3, autoscale to 5 |
| Monitoring tier | In-cluster kube-prometheus-stack + Loki |
| Secrets strategy | K8s native Secrets, pre-created by operator |
| Dapr install method | Helm chart with HA settings |

---

## Best Practices Referenced

- **DOKS**: DigitalOcean recommended node auto-scale group with min 2 nodes for HA
- **cert-manager**: ClusterIssuer with HTTP-01 challenge (no wildcard needed for 2 subdomains)
- **HPA**: Stabilization window 300s scale-down (prevents thrashing), 60s scale-up
- **Rolling update**: `maxSurge: 1, maxUnavailable: 0` — zero-downtime guarantee
- **Readiness probes**: 10s initial delay, 5s period, 3 failure threshold for backend pods with DB connection
- **Liveness probes**: 30s initial delay to avoid killing pods during startup

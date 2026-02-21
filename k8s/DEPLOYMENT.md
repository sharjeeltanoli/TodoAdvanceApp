# DOKS Deployment Guide — hackathon-todo

Complete operational guide for deploying the todo app to DigitalOcean Kubernetes (DOKS).

## Architecture

```
Internet
    │
    ▼
DigitalOcean Load Balancer (165.245.153.207)
    │
    ▼
ingress-nginx (namespace: ingress-nginx)
    │
    ├── todo-staging.165-245-153-207.nip.io  ──→  namespace: staging
    └── todo.<YOUR_DOMAIN>                   ──→  namespace: production
                                                   (future)
```

**Services per namespace:**
- `frontend`       — Next.js 16 (port 3000)
- `backend`        — FastAPI (port 8000) + Dapr sidecar
- `mcp`            — FastMCP server (port 8001) + Dapr sidecar
- `notification`   — Notification service (port 8002) + Dapr sidecar
- `sse-gateway`    — SSE streaming gateway (port 8003) + Dapr sidecar
- `redis`          — In-cluster Redis (Dapr state store)

**External services:**
- Neon Serverless PostgreSQL (shared DB)
- Redpanda Cloud (Kafka-compatible message broker, SASL/SCRAM-SHA-256)

---

## Prerequisites

```bash
kubectl version --client     # ≥ 1.28
helm version                 # ≥ 3.16
doctl version                # any recent version
```

Cluster kubeconfig already saved:
```bash
doctl kubernetes cluster kubeconfig save hackathon-todo
kubectl get nodes            # should show 1+ Ready nodes
```

---

## One-Time Cluster Bootstrap (already done)

| Component | Namespace | Status |
|---|---|---|
| ingress-nginx | ingress-nginx | ✅ Running (LB: 165.245.153.207) |
| cert-manager | cert-manager | ✅ Running |
| Dapr | dapr-system | ✅ Running (mTLS enabled) |
| ClusterIssuers | cluster-scoped | ✅ letsencrypt-prod + letsencrypt-staging READY |

---

## STEP 1 — Create Namespace (staging)

```bash
kubectl create namespace staging
kubectl apply -f k8s/cluster-bootstrap/dapr-configuration.yaml -n staging
```

---

## STEP 2 — Create Kubernetes Secrets

**⚠️ Never commit real secret values to git.**

Create the `app-secrets` secret in the staging namespace:

```bash
kubectl create secret generic app-secrets -n staging \
  --from-literal=DATABASE_URL="postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb?sslmode=require" \
  --from-literal=FRONTEND_DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require" \
  --from-literal=BETTER_AUTH_SECRET="$(openssl rand -hex 32)" \
  --from-literal=OPENAI_API_KEY="sk-..." \
  --from-literal=REDPANDA_BROKERS="seed-xxxxx.us-east-1.redpanda.com:9092" \
  --from-literal=REDPANDA_USERNAME="staging-todo-app" \
  --from-literal=REDPANDA_PASSWORD="<your-redpanda-password>" \
  --from-literal=REDPANDA_SASL_MECHANISM="SCRAM-SHA-256"
```

**Note on DATABASE_URL format:**
- `DATABASE_URL` → pooled connection with asyncpg prefix (`postgresql+asyncpg://...`)
- `FRONTEND_DATABASE_URL` → direct connection without asyncpg prefix (`postgresql://...`)

Create GHCR pull secret (to pull private images from GitHub Container Registry):
```bash
kubectl create secret docker-registry ghcr-pull-secret -n staging \
  --docker-server=ghcr.io \
  --docker-username=sharjeeltanoli \
  --docker-password=<GITHUB_PAT_READ_PACKAGES>
```

Verify:
```bash
kubectl get secret app-secrets -n staging
kubectl get secret ghcr-pull-secret -n staging
```

---

## STEP 3 — Deploy to Staging

```bash
# From repository root:
helm upgrade --install todo-app-staging chart/ \
  -f chart/values-staging.yaml \
  --namespace staging \
  --atomic \
  --timeout 10m \
  --wait
```

**What this does:**
- `--atomic` — rolls back automatically if any pod fails to become Ready
- `--timeout 10m` — allows time for image pulls on first deploy
- `--wait` — waits for all pods to be Running

---

## STEP 4 — Verify Deployment

```bash
# All pods Running
kubectl get pods -n staging

# Services
kubectl get svc -n staging

# Ingress + TLS
kubectl get ingress -n staging
kubectl describe ingress -n staging

# Certificate (takes ~2 min to issue)
kubectl get certificate -n staging
kubectl describe certificate -n staging

# Dapr sidecars injected
kubectl get pods -n staging -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{" "}{end}{"\n"}{end}'

# Dapr components registered
kubectl get components -n staging

# App logs
kubectl logs -n staging deployment/todo-app-staging-backend -c backend
kubectl logs -n staging deployment/todo-app-staging-backend -c daprd
```

---

## STEP 5 — Test Access

**HTTP test (direct IP — hostname header required):**
```bash
curl -H "Host: todo-staging.165-245-153-207.nip.io" http://165.245.153.207/health
```

**HTTPS test (after cert issued):**
```bash
# Staging cert has untrusted CA — use -k for testing
curl -k https://todo-staging.165-245-153-207.nip.io/health
curl -k https://todo-staging.165-245-153-207.nip.io/api/health
```

**Browser:**
Open `https://todo-staging.165-245-153-207.nip.io` (accept cert warning for staging ACME).

---

## Helm Upgrade (rolling updates)

```bash
# Deploy a specific image SHA
helm upgrade todo-app-staging chart/ \
  -f chart/values-staging.yaml \
  --namespace staging \
  --set global.imageTag=sha-abc1234 \
  --atomic --timeout 10m

# Check rollout status
kubectl rollout status deployment/todo-app-staging-backend -n staging
kubectl rollout status deployment/todo-app-staging-frontend -n staging
```

---

## Rollback

```bash
# List Helm history
helm history todo-app-staging -n staging

# Rollback to previous revision
helm rollback todo-app-staging -n staging

# Rollback to specific revision
helm rollback todo-app-staging 2 -n staging
```

---

## Teardown (staging)

```bash
helm uninstall todo-app-staging -n staging
kubectl delete namespace staging
```

---

## Troubleshooting

### Pods stuck in `ImagePullBackOff`
```bash
kubectl describe pod <pod-name> -n staging | grep -A5 Events
# → Check if ghcr-pull-secret exists and has correct credentials
kubectl get secret ghcr-pull-secret -n staging -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d
```

### Pods stuck in `CrashLoopBackOff`
```bash
kubectl logs <pod-name> -n staging --previous
# → Check for missing env vars (DATABASE_URL, BETTER_AUTH_SECRET, etc.)
kubectl describe secret app-secrets -n staging
```

### Dapr sidecar not injecting
```bash
kubectl get pods -n staging -o wide
# → Verify dapr-system pods are running
kubectl get pods -n dapr-system
# → Verify namespace has dapr.io/enabled annotation OR pod annotations are set
kubectl describe deployment todo-app-staging-backend -n staging | grep dapr
```

### Certificate not issuing
```bash
kubectl describe certificate -n staging
kubectl describe certificaterequest -n staging
kubectl describe order -n staging
kubectl logs -n cert-manager deployment/cert-manager | tail -50
# → Verify ingress is accessible from internet: curl http://todo-staging.165-245-153-207.nip.io/.well-known/acme-challenge/test
```

### Redpanda connection failures
```bash
# Check Dapr pubsub component
kubectl get components -n staging
kubectl describe component pubsub -n staging
# → Verify REDPANDA_BROKERS, REDPANDA_USERNAME, REDPANDA_PASSWORD in app-secrets
kubectl get secret app-secrets -n staging -o jsonpath='{.data.REDPANDA_BROKERS}' | base64 -d
```

### Redis not reachable
```bash
kubectl get svc -n staging | grep redis
kubectl exec -it deployment/todo-app-staging-backend -n staging -c daprd -- /bin/sh -c "wget -qO- http://localhost:3500/v1.0/metadata"
```

---

## Production Deployment (future)

1. Create `production` namespace + secrets (same process, different values)
2. Point DNS A-record for `todo.<YOUR_DOMAIN>` to `165.245.153.207`
3. Update `values-production.yaml` with your real domain
4. Change `ingress.certIssuer` to `letsencrypt-prod`
5. Deploy:
```bash
helm upgrade --install todo-app-production chart/ \
  -f chart/values-production.yaml \
  --namespace production \
  --atomic --timeout 10m
```

---

## Key File Locations

| File | Purpose |
|---|---|
| `chart/values-staging.yaml` | Staging overrides (nip.io host, single replica) |
| `chart/values-production.yaml` | Production overrides (HPA, monitoring enabled) |
| `chart/templates/` | Kubernetes manifest templates |
| `k8s/cluster-bootstrap/cluster-issuer.yaml` | Let's Encrypt ClusterIssuers |
| `k8s/cluster-bootstrap/dapr-configuration.yaml` | Dapr config (tracing, metrics) |
| `k8s/secrets/app-secrets.yaml` | Secret template (gitignored, fill & apply manually) |
| `.github/workflows/build.yml` | CI: build + push images to GHCR |
| `.github/workflows/deploy-staging.yml` | CD: auto-deploy to staging on main merge |
| `docs/runbooks/deploy.md` | Detailed cost + capacity runbook |
| `docs/runbooks/rollback.md` | Emergency rollback procedures |

---
id: "0009"
title: Phase 5C Full Staging Deploy
stage: green
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 006-cloud-deployment
branch: main
user: root
command: manual
labels: ["cloud-deployment","kubernetes","helm","staging","dapr","dockerfiles","ci-fix","nip.io","tls","letsencrypt"]
links:
  spec: specs/006-cloud-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - k8s/cluster-bootstrap/cluster-issuer.yaml
  - k8s/cluster-bootstrap/cert-manager-issuer.yaml
  - k8s/secrets/app-secrets.yaml
  - k8s/DEPLOYMENT.md
  - chart/templates/ingress.yaml
  - chart/templates/dapr-components.yaml
  - chart/values-staging.yaml
  - .gitignore
  - backend/Dockerfile
  - backend/Dockerfile.mcp
  - backend/Dockerfile.notification
  - backend/Dockerfile.sse-gateway
  - frontend/Dockerfile
  - .github/workflows/build.yml
tests:
  - "kubectl get clusterissuer → letsencrypt-prod READY=True, letsencrypt-staging READY=True"
  - "helm lint chart/ -f chart/values-staging.yaml → 0 failures"
  - "CI build-push (all 5 services) → success"
  - "kubectl get pods -n staging → all 6 pods 2/2 or 1/1 Running"
  - "kubectl get certificate -n staging → READY=True (TLS cert issued)"
  - "curl -sk https://todo-staging.165-245-153-207.nip.io/api/todos → {detail:Not authenticated}"
  - "curl http://todo-staging.165-245-153-207.nip.io → 308 redirect to HTTPS"
  - "kubectl get components -n staging → pubsub, statestore, cron-overdue-check present"
---

## Prompt

Complete Phase 5C cloud deployment on DigitalOcean Kubernetes.
CURRENT STATUS: ✅ DOKS cluster (1 node), ✅ ingress-nginx (165.245.153.207), ✅ cert-manager, ✅ Dapr (mTLS)

## Response snapshot

Completed full staging deployment. Required fixing 6 issues discovered during the process:

**Issue 1 — gitleaks-action SHA invalid**: Build workflow had pinned SHAs pointing to non-existent commits. Removed SHA pinning, switched to version tags (@v4, @v5).

**Issue 2 — `requirements.txt` missing**: Backend uses pyproject.toml. Fixed CI test step to `pip install -e ".[dev]"`.

**Issue 3 — Dockerfiles missing**: All 5 Dockerfiles created:
- `backend/Dockerfile` → `uvicorn app.main:app :8000`
- `backend/Dockerfile.mcp` → `uvicorn mcp_server.server:app :8001`
- `backend/Dockerfile.notification` → `uvicorn services.notification.main:app :8002`
- `backend/Dockerfile.sse-gateway` → `uvicorn services.sse_gateway.main:app :8003`
- `frontend/Dockerfile` → Next.js standalone build :3000

**Issue 4 — Dapr Configuration mtls invalid**: `spec.mtls` block not valid in app-level Configuration (it's cluster-plane only). Removed the mtls section.

**Issue 5 — Duplicate kubernetes secret store**: Dapr 1.16 auto-registers the kubernetes secret store; defining it in the chart caused "component already exists" fatal crash. Removed the explicit Component definition.

**Issue 6 — authType 'scram' invalid in Dapr 1.16**: Kafka pubsub authType was `scram` (old value). Changed to `scramsha256` (Dapr 1.14+ value). Added `ignoreErrors: true` so pods don't crash when Redpanda isn't configured yet.

**Issue 7 — bare Python imports**: `notification/main.py` uses `from models import` and `sse_gateway/main.py` uses `from connections import` — bare imports that need the service directory on PYTHONPATH. Added `ENV PYTHONPATH=/app/services/<name>:/app` to each Dockerfile.

**Kubernetes secrets created (live, not committed):**
- `app-secrets` — DATABASE_URL (asyncpg pooler), FRONTEND_DATABASE_URL (direct), BETTER_AUTH_SECRET, OPENAI_API_KEY, REDPANDA_* (placeholders — user to update after Redpanda setup)
- `ghcr-pull-secret` — GHCR pull credentials

**Final state:**
- All 6 pods Running: backend 2/2, frontend 1/1, mcp 2/2, notification 2/2, sse-gateway 2/2, redis 1/1
- Ingress: `todo-staging.165-245-153-207.nip.io` → 165.245.153.207
- TLS: letsencrypt-staging cert READY=True
- HTTPS: `{"detail":"Not authenticated"}` ← correct (auth required)
- HTTP→HTTPS: 308 redirect working

**Pending (user action required):**
- Set up Redpanda Cloud → update `app-secrets` with real REDPANDA_BROKERS/USERNAME/PASSWORD
- Switch `ingress.certIssuer` from `letsencrypt-staging` to `letsencrypt-prod` for production-grade cert

## Outcome

- ✅ Impact: Full staging deployment live at https://todo-staging.165-245-153-207.nip.io
- 🧪 Tests: All 6 pods Running, TLS Ready, HTTPS responding correctly
- 📁 Files: 14 created/modified
- 🔁 Next: Set up Redpanda Cloud, update k8s secret, upgrade helm release with real Redpanda creds

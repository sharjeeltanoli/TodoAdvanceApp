---
id: "0008"
title: Phase 5C Cluster Deploy Steps 1-3
stage: green
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 006-cloud-deployment
branch: main
user: root
command: manual
labels: ["cloud-deployment","kubernetes","cert-manager","lets-encrypt","helm","staging","secrets","redpanda"]
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
  - chart/values-staging.yaml
  - .gitignore
tests:
  - "kubectl get clusterissuer → letsencrypt-prod READY=True, letsencrypt-staging READY=True"
  - "helm lint chart/ -f chart/values-staging.yaml → 0 failures"
  - "kubectl apply dapr-configuration.yaml -n staging → configuration.dapr.io/appconfig created"
---

## Prompt

Complete Phase 5C cloud deployment on DigitalOcean Kubernetes.

CURRENT STATUS:
✅ DOKS cluster running (1 node)
✅ ingress-nginx installed (EXTERNAL-IP: 165.245.153.207)
✅ cert-manager installed
✅ Dapr installed (mTLS enabled)

REMAINING TASKS: STEP 1-6 (ClusterIssuer, Redpanda setup, secrets, staging deploy, verify, DEPLOYMENT.md)

## Response snapshot

Executed Steps 1, 3 (partial), and 6. Paused at Step 3 for user to provide secret values.

**Files created:**
- `k8s/cluster-bootstrap/cluster-issuer.yaml` — Both letsencrypt-prod and letsencrypt-staging ClusterIssuers with email sharjeeel3@gmail.com
- `k8s/secrets/app-secrets.yaml` — Secret manifest template (gitignored), with placeholder values for all 8 required secrets
- `k8s/DEPLOYMENT.md` — Complete operational deployment guide including troubleshooting

**Files modified:**
- `k8s/cluster-bootstrap/cert-manager-issuer.yaml` — Filled in email sharjeeel3@gmail.com
- `chart/templates/ingress.yaml` — Made cert-issuer configurable via `.Values.ingress.certIssuer` (defaults to letsencrypt-prod)
- `chart/values-staging.yaml` — Replaced `<OWNER>` with `sharjeeltanoli`, `<DOMAIN>` with `165-245-153-207.nip.io`; set `ingress.certIssuer: letsencrypt-staging`
- `.gitignore` — Added `k8s/secrets/app-secrets.yaml` to prevent secret commits

**Applied to cluster:**
- ClusterIssuers: letsencrypt-prod + letsencrypt-staging → both READY=True
- Dapr appconfig → applied to staging namespace

**Pending (waiting for user inputs):**
- Actual secret values (DATABASE_URL, OPENAI_API_KEY, BETTER_AUTH_SECRET, FRONTEND_DATABASE_URL, REDPANDA_*)
- `kubectl create secret generic app-secrets -n staging ...`
- `kubectl create secret docker-registry ghcr-pull-secret -n staging ...`
- `helm upgrade --install todo-app-staging chart/ -f chart/values-staging.yaml -n staging --atomic --timeout 10m`

## Outcome

- ✅ Impact: ClusterIssuers ready; chart validated (helm lint passes); staging namespace + Dapr config created
- 🧪 Tests: 2 ClusterIssuers READY, helm lint 0 failures, Dapr config applied
- 📁 Files: 3 created, 4 modified
- 🔁 Next: User provides secret values → create k8s secrets → helm deploy → verify

# Cluster Bootstrap — One-Time Setup

Run these steps **once** when first provisioning the DOKS cluster.
All commands are idempotent — safe to re-run if interrupted.

## Prerequisites

- `doctl` installed and authenticated (`doctl auth init`)
- `kubectl` installed (≥ 1.28)
- `helm` installed (≥ 3.16)
- DigitalOcean account with $200 credit applied
- Domain with DNS A-record control

---

## Step 1 — Provision DOKS Cluster (T005)

```bash
doctl kubernetes cluster create hackathon-todo \
  --region nyc1 \
  --node-pool "name=default;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=3;max-nodes=5" \
  --version latest \
  --wait

doctl kubernetes cluster kubeconfig save hackathon-todo
kubectl get nodes  # verify 3 nodes Ready
```

**Cost**: ~$84/mo (3 nodes + 1 LB). Full cost breakdown: `docs/runbooks/deploy.md`.

---

## Step 2 — Add Helm Repositories (T006)

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add jetstack https://charts.jetstack.io
helm repo add dapr https://dapr.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add azure https://charts.helm.sh/stable  # for azure/setup-helm
helm repo update
```

---

## Step 3 — Install ingress-nginx (T007)

```bash
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.replicaCount=2 \
  --set controller.metrics.enabled=true \
  --set controller.metrics.serviceMonitor.enabled=true

# Wait for EXTERNAL-IP (takes ~60s for DigitalOcean LB provisioning)
kubectl get svc ingress-nginx-controller -n ingress-nginx --watch
# → Record the EXTERNAL-IP for DNS configuration below
```

**DNS** (required before cert issuance):
```
A  todo.<DOMAIN>          →  <LB-IP>
A  staging.todo.<DOMAIN>  →  <LB-IP>
```

---

## Step 4 — Install cert-manager (T008)

```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true \
  --set prometheus.enabled=true

# Fill operator email then apply ClusterIssuer
sed -i 's/<OPERATOR_EMAIL>/your@email.com/' k8s/cluster-bootstrap/cert-manager-issuer.yaml
kubectl apply -f k8s/cluster-bootstrap/cert-manager-issuer.yaml
```

> ⚠️ DNS A records (Step 3) MUST propagate before cert-manager issues certificates.
> Use `dig staging.todo.<DOMAIN>` to verify propagation.

---

## Step 5 — Install Dapr (T009)

```bash
helm install dapr dapr/dapr \
  --namespace dapr-system --create-namespace \
  --set global.ha.enabled=true \
  --set global.mtls.enabled=true \
  --wait

kubectl get pods -n dapr-system  # verify all control-plane pods Running
```

---

## Step 6 — Install Monitoring Stack (T010)

```bash
# Prometheus + Grafana + AlertManager
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword="<GRAFANA_PASSWORD>" \
  --set prometheus.prometheusSpec.retention=30d \
  --set "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=20Gi" \
  --set "alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=5Gi"

# Loki + Promtail
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=20Gi
```

---

## Step 7 — Redpanda Cloud Setup (T011, T012)

1. Sign up at https://cloud.redpanda.com → Create cluster → **Serverless (Free)**
2. Region: `us-east-1` (closest to `nyc1`)
3. Create topics:
   - Production: `task-events`, `notifications`, `processed-events`
   - Staging: `staging-task-events`, `staging-notifications`, `staging-processed-events`
4. Create service accounts:
   - `production-todo-app` — ACL: Read/Write on production topics
   - `staging-todo-app` — ACL: Read/Write on `staging-*` topics
5. Record: broker URL, usernames, passwords (SASL/SCRAM-SHA-256)

---

## Step 8 — Create Namespaces and Secrets (T013, T014, T015)

```bash
# Production namespace + app secrets
kubectl create namespace production
kubectl create secret generic app-secrets -n production \
  --from-literal=DATABASE_URL="<neon-prod-url>" \
  --from-literal=BETTER_AUTH_SECRET="<secret>" \
  --from-literal=OPENAI_API_KEY="<key>" \
  --from-literal=FRONTEND_DATABASE_URL="<neon-direct-url>" \
  --from-literal=REDPANDA_BROKERS="<redpanda-cloud-brokers>" \
  --from-literal=REDPANDA_USERNAME="<prod-username>" \
  --from-literal=REDPANDA_PASSWORD="<prod-password>" \
  --from-literal=REDPANDA_SASL_MECHANISM="SCRAM-SHA-256"

# GHCR pull secret (production)
kubectl create secret docker-registry ghcr-pull-secret -n production \
  --docker-server=ghcr.io \
  --docker-username=<GITHUB_USER> \
  --docker-password=<GITHUB_PAT_READ_PACKAGES>

# Repeat for staging namespace (different values)
kubectl create namespace staging
kubectl create secret generic app-secrets -n staging \
  --from-literal=DATABASE_URL="<neon-staging-url>" \
  --from-literal=BETTER_AUTH_SECRET="<staging-secret>" \
  --from-literal=OPENAI_API_KEY="<key>" \
  --from-literal=FRONTEND_DATABASE_URL="<neon-staging-direct-url>" \
  --from-literal=REDPANDA_BROKERS="<redpanda-cloud-brokers>" \
  --from-literal=REDPANDA_USERNAME="<staging-username>" \
  --from-literal=REDPANDA_PASSWORD="<staging-password>" \
  --from-literal=REDPANDA_SASL_MECHANISM="SCRAM-SHA-256"

kubectl create secret docker-registry ghcr-pull-secret -n staging \
  --docker-server=ghcr.io \
  --docker-username=<GITHUB_USER> \
  --docker-password=<GITHUB_PAT_READ_PACKAGES>

# Apply Dapr configuration to both namespaces
kubectl apply -f k8s/cluster-bootstrap/dapr-configuration.yaml -n staging
kubectl apply -f k8s/cluster-bootstrap/dapr-configuration.yaml -n production
```

---

## Checkpoint

```bash
kubectl get nodes                           # 3 nodes Ready
kubectl get pods -n ingress-nginx           # ingress-nginx-controller Running
kubectl get pods -n cert-manager            # 3 cert-manager pods Running
kubectl get pods -n dapr-system             # 5+ dapr pods Running
kubectl get pods -n monitoring              # prometheus, grafana, loki Running
kubectl get clusterissuer letsencrypt-prod  # READY=True
kubectl get secret app-secrets -n staging  # exists
kubectl get secret app-secrets -n production  # exists
```

All checks passing → proceed to first deployment via GitHub Actions (push to `main`).

# Cloud Deployment Blueprint Skill

## When to Use This Skill

**Triggers:**
- User asks to deploy to cloud / production / staging
- User mentions DigitalOcean, DOKS, AKS, GKE, or cloud Kubernetes
- User wants CI/CD pipeline for Docker + Kubernetes
- User asks about SSL, autoscaling, or production readiness
- User says "deploy to cloud", "production deployment", "set up CI/CD"
- Phase 5C cloud deployment work

## Cloud Provider Comparison

| Feature | DigitalOcean DOKS | Azure AKS | Google GKE |
|---------|-------------------|-----------|------------|
| **Min Cost** | ~$24/mo (2-node) | ~$73/mo (free control plane) | ~$73/mo (free autopilot) |
| **Setup Complexity** | Low | Medium | Medium |
| **Managed Registry** | DOCR ($5/mo) | ACR (included) | GCR/AR (included) |
| **Load Balancer** | $12/mo | ~$20/mo | ~$18/mo |
| **Free Tier** | $200 credit (60d) | $200 credit | $300 credit (90d) |
| **Best For** | Hackathons, startups | Enterprise, Azure shops | ML/AI, large scale |
| **CLI** | `doctl` | `az` | `gcloud` |

**Recommendation for hackathons:** DigitalOcean DOKS — simplest setup, lowest cost, fastest provisioning (~4 min).

## DigitalOcean DOKS Setup

### Prerequisites
```bash
# Install doctl CLI
brew install doctl   # macOS
snap install doctl   # Linux

# Authenticate
doctl auth init --access-token $DIGITALOCEAN_TOKEN

# Install kubectl
brew install kubectl
```

### Create Cluster
```bash
# Create a 2-node cluster (cheapest production-viable)
doctl kubernetes cluster create hackathon-todo \
  --region nyc1 \
  --node-pool "name=default;size=s-2vcpu-4gb;count=2;auto-scale=true;min-nodes=2;max-nodes=5" \
  --version latest

# Save kubeconfig
doctl kubernetes cluster kubeconfig save hackathon-todo

# Verify
kubectl get nodes
```

### Create Container Registry (DOCR)
```bash
# Create registry (starter tier = free, 500MB)
doctl registry create hackathon-todo --subscription-tier starter

# Login Docker to registry
doctl registry login

# Connect registry to cluster
doctl registry kubernetes-manifest | kubectl apply -f -
```

## GitHub Actions CI/CD Pipeline

### Pipeline Architecture
```
PR opened/updated → Build images → Push to GHCR → Deploy to staging
Merge to main    → Build images → Push to GHCR → Deploy to production
```

### Required GitHub Secrets
```
DIGITALOCEAN_ACCESS_TOKEN  - DO API token
KUBE_CONFIG_DATA           - base64-encoded kubeconfig
```

### Using GHCR (Free)
GitHub Container Registry is free for public repos and included in GitHub plans for private repos.

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Image naming: ghcr.io/OWNER/REPO/SERVICE:TAG
# Example: ghcr.io/myorg/hackathon-todo/backend:v1.0.0
```

## Docker Image Strategy

### Multi-stage Builds
- **Frontend:** Node build → nginx serve (final ~50MB)
- **Backend:** Python deps → slim runtime (final ~150MB)
- **MCP Server:** Python deps → slim runtime (final ~120MB)

### Tagging Strategy
```
ghcr.io/OWNER/hackathon-todo/frontend:sha-abc1234   # commit SHA
ghcr.io/OWNER/hackathon-todo/frontend:pr-42          # PR number
ghcr.io/OWNER/hackathon-todo/frontend:latest          # latest main
ghcr.io/OWNER/hackathon-todo/frontend:v1.2.3          # release tag
```

## Helm Deployment

### Install Helm
```bash
brew install helm   # macOS
snap install helm   # Linux
```

### Deploy with Helm
```bash
# Staging
helm upgrade --install hackathon-todo ./deploy/helm/hackathon-todo \
  -f ./deploy/helm/hackathon-todo/values-staging.yaml \
  --namespace staging --create-namespace \
  --set image.tag=$IMAGE_TAG

# Production
helm upgrade --install hackathon-todo ./deploy/helm/hackathon-todo \
  -f ./deploy/helm/hackathon-todo/values-production.yaml \
  --namespace production --create-namespace \
  --set image.tag=$IMAGE_TAG
```

## SSL/TLS with cert-manager

### Install cert-manager
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true
```

### How It Works
1. Deploy `ClusterIssuer` pointing to Let's Encrypt
2. Add annotation to Ingress: `cert-manager.io/cluster-issuer: letsencrypt-prod`
3. cert-manager auto-provisions and renews TLS certificates

## Horizontal Pod Autoscaling (HPA)

### How It Works
- Monitors CPU/memory utilization per pod
- Scales replicas between min and max based on thresholds
- Requires `metrics-server` (pre-installed on DOKS)

### Configuration
```yaml
# Scale when CPU > 70%
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

## Production vs Staging Environments

| Aspect | Staging | Production |
|--------|---------|------------|
| **Namespace** | `staging` | `production` |
| **Replicas** | 1 | 2-3 |
| **CPU Request** | 100m | 250m |
| **Memory Request** | 128Mi | 256Mi |
| **HPA** | Disabled | Enabled |
| **Domain** | staging.app.example.com | app.example.com |
| **TLS** | Let's Encrypt staging | Let's Encrypt prod |
| **Deploy trigger** | PR branch push | Merge to main |

## Rolling Deployments

Default Kubernetes rolling update strategy:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # 1 extra pod during update
    maxUnavailable: 0  # zero downtime
```

Combined with readiness probes, this ensures:
1. New pod starts and passes health check
2. Traffic routes to new pod
3. Old pod is terminated
4. Repeat until all pods updated

## Monitoring and Logging

### Basic (kubectl)
```bash
# Pod status
kubectl get pods -n production

# Logs
kubectl logs -f deployment/backend -n production

# Events (troubleshooting)
kubectl get events -n production --sort-by=.lastTimestamp

# Resource usage
kubectl top pods -n production
kubectl top nodes
```

### DigitalOcean Monitoring (Free)
- Built-in cluster monitoring dashboard
- CPU, memory, disk metrics per node
- Alert policies via DO console

### Advanced (Optional)
```bash
# Install kube-prometheus-stack for Grafana + Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

## Cost Optimization

### Cluster Sizing
| Setup | Monthly Cost | Use Case |
|-------|-------------|----------|
| 2x s-1vcpu-2gb | ~$24 | Development/demo |
| 2x s-2vcpu-4gb | ~$48 | Staging/small prod |
| 3x s-4vcpu-8gb | ~$144 | Production |

### Tips
- Use node auto-scaling (min 2, max 5)
- Set resource requests/limits on all pods
- Use `Burstable` QoS class for non-critical services
- Schedule non-prod cluster downtime with CronJobs
- Use GHCR (free) instead of paid registries
- Single load balancer with Ingress (not per-service LBs)

## Rollback Strategies

### Helm Rollback
```bash
# List releases
helm history hackathon-todo -n production

# Rollback to previous
helm rollback hackathon-todo -n production

# Rollback to specific revision
helm rollback hackathon-todo 3 -n production
```

### Kubernetes Rollback
```bash
# Check rollout history
kubectl rollout history deployment/backend -n production

# Undo last rollout
kubectl rollout undo deployment/backend -n production

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n production
```

### Emergency: Quick Image Revert
```bash
kubectl set image deployment/backend \
  backend=ghcr.io/OWNER/hackathon-todo/backend:KNOWN_GOOD_TAG \
  -n production
```

## Quick Start (Hackathon Mode)

```bash
# 1. Set up DOKS cluster
doctl kubernetes cluster create hackathon-todo \
  --region nyc1 \
  --node-pool "name=default;size=s-2vcpu-4gb;count=2" \
  --version latest

# 2. Install ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# 3. Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# 4. Deploy app
helm upgrade --install hackathon-todo ./deploy/helm/hackathon-todo \
  -f ./deploy/helm/hackathon-todo/values-production.yaml \
  --namespace production --create-namespace

# 5. Get external IP
kubectl get svc -n ingress-nginx
# Point your domain DNS A record to this IP

# 6. Verify
curl https://app.example.com/api/health
```

## Template Files

| Template | Purpose |
|----------|---------|
| `digitalocean-cluster.yaml.template` | DOKS cluster IaC config |
| `github-actions-build.yaml.template` | CI: build + push Docker images |
| `github-actions-deploy.yaml.template` | CD: deploy to K8s via Helm |
| `helm-values-production.yaml.template` | Production Helm overrides |
| `helm-values-staging.yaml.template` | Staging Helm overrides |
| `kubernetes-ingress-prod.yaml.template` | Ingress with TLS |
| `cert-manager-issuer.yaml.template` | Let's Encrypt ClusterIssuer |
| `horizontal-pod-autoscaler.yaml.template` | HPA for auto-scaling |

## Example Files

| Example | Purpose |
|---------|---------|
| `digitalocean-doks-example.yaml` | Complete DOKS setup with doctl |
| `full-cicd-pipeline-example.yaml` | End-to-end GitHub Actions pipeline |
| `production-values-example.yaml` | Real-world production Helm values |

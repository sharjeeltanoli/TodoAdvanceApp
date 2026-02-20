# Deployment Runbook

**Cluster**: DOKS `hackathon-todo` (nyc1) | **Registry**: GHCR | **Cost**: ~$88.50/mo

---

## Normal Deploy Flow (automated)

### Staging — on every push to `main`

1. Developer merges PR → `main`
2. GitHub Actions `build.yml` triggers automatically:
   - Scans for leaked secrets (gitleaks)
   - Runs backend tests (pytest) + frontend type-check
   - Helm lints staging + production values
   - Builds and pushes 5 service images to GHCR (tagged `sha-<7-char>` + `main-latest`)
3. `deploy-staging.yml` triggers on `build.yml` success:
   - Authenticates to DOKS via `doctl`
   - Runs `helm upgrade --install --atomic --timeout 5m`
   - Verifies rollout with `kubectl rollout status`
4. Target: all 5 pods Running in `staging` namespace within **10 minutes** of merge

### Production — on GitHub Release tag

1. Developer creates a GitHub Release with tag `v1.x.x`
2. `deploy-production.yml` triggers:
   - Requires **manual approval** in GitHub → Settings → Environments → production
   - Authenticates to DOKS, runs `helm upgrade --install --atomic --timeout 10m`
   - Smoke-tests `https://todo.<DOMAIN>/api/health`
3. Target: zero-downtime rollout within **10 minutes** of approval

---

## Manual Deploy Commands

```bash
# Staging manual deploy (replace sha-xxxxxxx with actual tag)
helm upgrade --install todo-app-staging ./chart \
  -f ./chart/values-staging.yaml \
  --namespace staging \
  --set global.imageTag=sha-xxxxxxx \
  --atomic --timeout 5m --history-max 10

# Production manual deploy (replace v1.0.0 with release tag)
helm upgrade --install todo-app ./chart \
  -f ./chart/values-production.yaml \
  --namespace production \
  --set global.imageTag=v1.0.0 \
  --atomic --timeout 10m --history-max 10
```

---

## Environment Isolation Verification

```bash
# Confirm staging and production have independent release histories
helm history todo-app-staging -n staging
helm history todo-app -n production

# Confirm secrets differ between environments
kubectl get secret app-secrets -n staging -o yaml | grep -A5 data:
kubectl get secret app-secrets -n production -o yaml | grep -A5 data:

# Dry-run: confirm staging upgrade does NOT touch production
helm upgrade todo-app-staging ./chart -f chart/values-staging.yaml \
  --namespace staging --dry-run | grep namespace
# Expected: only "staging" appears in output
```

---

## GitHub Secrets and Variables Required

| Name | Type | Purpose |
|------|------|---------|
| `DIGITALOCEAN_ACCESS_TOKEN` | Secret | `doctl` authentication |
| `vars.DOMAIN` | Variable | Base domain (e.g., `example.com`) |
| Production environment | Environments setting | Manual approval gate |

**Configure in**: GitHub → Settings → Secrets and variables → Actions

---

## Resource Quotas (applied in T043)

```bash
# Staging
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: staging-quota
  namespace: staging
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 6Gi
    limits.cpu: "8"
    limits.memory: 12Gi
EOF

# Production
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 12Gi
    limits.cpu: "16"
    limits.memory: 24Gi
EOF
```

---

## Cost Monitoring

**Monthly estimate**: ~$88.50

| Resource | Size | Monthly |
|----------|------|---------|
| DOKS nodes (3×) | s-2vcpu-4gb | $72.00 |
| DigitalOcean Load Balancer (1×) | Standard | $12.00 |
| Prometheus PVC | 20 GB | $2.00 |
| Loki PVC | 20 GB | $2.00 |
| AlertManager PVC | 5 GB | $0.50 |
| Redpanda Cloud | Free tier | $0.00 |
| GHCR | Free | $0.00 |
| **Total** | | **~$88.50/mo** |

**$200 credit runway**: ~2.3 months

**Save costs overnight** (scale staging to 0):
```bash
kubectl scale deployment --all -n staging --replicas=0
# Restore next morning:
kubectl scale deployment --all -n staging --replicas=1
```

**DigitalOcean billing dashboard**: https://cloud.digitalocean.com/account/billing

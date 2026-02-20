# Rollback Runbook

Target: restore previous working version within **5 minutes** (SC-007).

---

## Option 1 — Helm Rollback (preferred, < 5 min)

```bash
# List production revision history
helm history todo-app -n production

# Roll back to previous revision (most common case)
helm rollback todo-app -n production --wait --timeout 5m

# Roll back to specific revision number
helm rollback todo-app 3 -n production --wait --timeout 5m
```

Helm rollback replaces the full release — all 5 services revert simultaneously.

---

## Option 2 — kubectl rollout undo (single deployment, < 2 min)

```bash
# Roll back a single deployment (e.g., backend only)
kubectl rollout undo deployment/todo-app-backend -n production

# Verify the rollback
kubectl rollout status deployment/todo-app-backend -n production

# Check which image is now running
kubectl get deployment todo-app-backend -n production \
  -o jsonpath='{.spec.template.spec.containers[0].image}'
```

---

## Option 3 — Emergency image revert (< 1 min)

Use when you know the exact last-good image tag:

```bash
# Replace <KNOWN_GOOD_TAG> with e.g. sha-a1b2c3d or v1.0.0
kubectl set image deployment/todo-app-backend \
  backend=ghcr.io/<OWNER>/hackathon-todo/backend:<KNOWN_GOOD_TAG> \
  -n production

kubectl rollout status deployment/todo-app-backend -n production
```

Repeat for each service if needed (frontend, mcp, notification, sse-gateway).

---

## Automatic Rollback via `--atomic`

Both staging and production pipelines use `helm upgrade --atomic`.
If any pod fails its readiness probe within the timeout, Helm **automatically rolls back**
to the previous release — no manual intervention required.

---

## Staging Rollback

```bash
helm history todo-app-staging -n staging
helm rollback todo-app-staging -n staging --wait --timeout 3m
```

---

## Verify After Rollback

```bash
# Health check
curl -f https://todo.<DOMAIN>/api/health

# Confirm pod versions
kubectl get pods -n production -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'

# Check Helm release status
helm status todo-app -n production
```

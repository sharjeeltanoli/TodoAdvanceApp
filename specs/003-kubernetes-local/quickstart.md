# Quickstart: Local Kubernetes Deployment

**Feature**: 003-kubernetes-local | **Date**: 2026-02-15

## Prerequisites

1. **Docker** — Docker Desktop or Docker Engine installed and running
2. **Minikube** >= 1.33 — `brew install minikube` or [install guide](https://minikube.sigs.k8s.io/docs/start/)
3. **Helm** >= 3.14 — `brew install helm` or [install guide](https://helm.sh/docs/intro/install/)
4. **kubectl** >= 1.29 — Usually bundled with Minikube
5. **Neon Database URL** — Your PostgreSQL connection string from Neon

## One-Command Setup (Recommended)

```bash
export DATABASE_URL="your-neon-db-url"
export FRONTEND_DATABASE_URL="your-neon-db-url-standard"
export BETTER_AUTH_SECRET="$(openssl rand -base64 32)"
export OPENAI_API_KEY="your-openai-key"
# Optional: export OPENAI_BASE_URL="https://custom-endpoint"

./scripts/minikube-setup.sh
```

This handles everything: starts Minikube, builds images, deploys with Helm, and waits for pods.

---

## Manual Deploy (5 steps)

### 1. Start Minikube

```bash
minikube start --cpus=4 --memory=8192 --driver=docker
```

### 2. Point Docker to Minikube

```bash
eval $(minikube docker-env)
```

### 3. Build Images

```bash
# From repository root
docker build -f Dockerfile.frontend -t todo-frontend:latest ./frontend
docker build -f Dockerfile.backend  -t todo-backend:latest  ./backend
docker build -f Dockerfile.mcp      -t todo-mcp:latest      ./backend
```

### 4. Deploy with Helm

```bash
helm install todo-app ./chart \
  --namespace todo-app \
  --create-namespace \
  --set secrets.databaseUrl="YOUR_NEON_DATABASE_URL" \
  --set secrets.frontendDatabaseUrl="YOUR_NEON_DATABASE_URL_STANDARD_FORMAT" \
  --set secrets.betterAuthSecret="$(openssl rand -base64 32)" \
  --set secrets.openaiApiKey="YOUR_OPENAI_API_KEY"
```

### 5. Access the App

```bash
# Get the frontend URL
minikube service todo-app-frontend -n todo-app --url

# Or use the fixed NodePort
# Open http://localhost:30080 (may need minikube tunnel on some setups)
```

## Verify Deployment

```bash
# All pods should show Running (1/1)
kubectl get pods -n todo-app

# Expected output:
# NAME                                  READY   STATUS    RESTARTS   AGE
# todo-app-frontend-xxxxx               1/1     Running   0          60s
# todo-app-backend-xxxxx                1/1     Running   0          60s
# todo-app-mcp-xxxxx                    1/1     Running   0          60s
```

## Common Operations

### Upgrade after code changes

```bash
# Rebuild changed images
eval $(minikube docker-env)
docker build -f Dockerfile.frontend -t todo-frontend:latest ./frontend

# Restart pods to pick up new image
kubectl rollout restart deployment/todo-app-frontend -n todo-app
```

### View logs

```bash
kubectl logs -f -l app.kubernetes.io/component=frontend -n todo-app
kubectl logs -f -l app.kubernetes.io/component=backend -n todo-app
kubectl logs -f -l app.kubernetes.io/component=mcp -n todo-app
```

### Rollback

```bash
helm rollback todo-app 1 -n todo-app
```

### Teardown

```bash
helm uninstall todo-app -n todo-app
kubectl delete namespace todo-app
minikube stop
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ImagePullBackOff` | Run `eval $(minikube docker-env)` and rebuild |
| `CrashLoopBackOff` | Check logs: `kubectl logs <pod> -n todo-app` |
| Can't access frontend | Try `minikube service todo-app-frontend -n todo-app --url` |
| DB connection error | Verify `secrets.databaseUrl` is correct |

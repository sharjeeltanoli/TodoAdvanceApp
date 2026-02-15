# Implementation Plan: Local Kubernetes Deployment

**Branch**: `003-kubernetes-local` | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-kubernetes-local/spec.md`

## Summary

Deploy the full Todo Chatbot stack (Next.js frontend, FastAPI backend, FastMCP server) to a local Minikube cluster using Docker multi-stage builds and a single Helm chart. All three services are containerized separately, orchestrated via Helm, and exposed through NodePort (frontend) and ClusterIP (backend, MCP) services. The external Neon PostgreSQL database is used as-is — no in-cluster database.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), Python 3.13 (backend + MCP)
**Primary Dependencies**: Next.js 16.1.6, FastAPI 0.115.8, FastMCP (MCP SDK v1.26.0)
**Storage**: External Neon Serverless PostgreSQL (shared by all services, no in-cluster DB)
**Testing**: Manual smoke tests (helm install → kubectl get pods → browser access)
**Target Platform**: Local Minikube on Linux/macOS/WSL2 (4 CPU, 8GB RAM)
**Project Type**: Web (monorepo: `frontend/` + `backend/`)
**Performance Goals**: All pods Running within 120s of `helm install`
**Constraints**: Images built into Minikube's Docker daemon (no remote registry); < 500MB per image
**Scale/Scope**: Single replica per service for local development

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | PASS | spec.md exists; plan.md being generated; tasks.md next |
| II. Monorepo Structure | PASS | Dockerfiles and chart at repo root; `frontend/` and `backend/` preserved |
| III. Stateless Services | PASS | All state in external Neon DB; pods are fully stateless |
| IV. Event-Driven Architecture | N/A | Kafka/Dapr deferred to Phase 5 |
| V. User Isolation | PASS | Existing user_id filtering unchanged; K8s layer is transparent |
| VI. MCP Protocol | PASS | MCP server deployed as separate pod with own service |
| Security: JWT auth | PASS | Auth flows unchanged; secrets in K8s Secrets, not ConfigMaps |
| Security: No hardcoded secrets | PASS | All secrets via `values.yaml` → K8s Secrets → env vars |
| Security: Non-root containers | PASS | All Dockerfiles run as UID 1001 non-root user |

## Project Structure

### Documentation (this feature)

```text
specs/003-kubernetes-local/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (K8s resource model)
├── quickstart.md        # Phase 1 output (developer setup guide)
└── tasks.md             # Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
# Dockerfiles (at repo root, one per service)
Dockerfile.frontend          # Multi-stage Next.js build
Dockerfile.backend           # Multi-stage FastAPI build
Dockerfile.mcp               # Multi-stage MCP server build
.dockerignore                # Shared build-context exclusions

# Helm chart (at repo root)
chart/
├── Chart.yaml               # Chart metadata (todo-app v0.1.0)
├── values.yaml              # Default values for Minikube
├── templates/
│   ├── _helpers.tpl          # Shared template helpers
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── mcp-deployment.yaml
│   ├── mcp-service.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── ingress.yaml          # Optional, disabled by default
│   └── NOTES.txt             # Post-install instructions
└── .helmignore

# Developer scripts
scripts/
└── minikube-setup.sh         # One-command cluster + build + deploy
```

**Structure Decision**: Dockerfiles at repo root (each references `frontend/` or `backend/` context). Helm chart in `chart/` directory at repo root. This follows the monorepo principle — everything deployable is co-located.

---

## Architecture

### 1. Docker Images Architecture

Three separate images, each with multi-stage builds:

| Image | Base | Build Stage | Runtime Stage | Port | Size Target |
|-------|------|-------------|---------------|------|-------------|
| `todo-frontend` | `node:22-alpine` | Install deps + `next build` (standalone) | `node:22-alpine` with standalone output | 3000 | < 300MB |
| `todo-backend` | `python:3.13-slim` | Install deps via pip | `python:3.13-slim` with app code | 8000 | < 400MB |
| `todo-mcp` | `python:3.13-slim` | Install deps via pip | `python:3.13-slim` with mcp_server code | 8001 | < 400MB |

**Key decisions:**
- **Standalone output for Next.js**: `next.config.ts` must add `output: "standalone"` to enable minimal production build without `node_modules`
- **Shared Python base for backend + MCP**: Both use `python:3.13-slim` (not alpine, due to musl issues with asyncpg/greenlet)
- **MCP server shares `backend/` build context**: The MCP server code lives in `backend/mcp_server/`, so `Dockerfile.mcp` uses `backend/` as context but only copies `mcp_server/` and its dependencies

### 2. Dockerfile Specifications

#### 2a. Dockerfile.frontend

```
Stage 1 (deps):    node:22-alpine → npm ci (production + dev deps for build)
Stage 2 (build):   Copy source → next build (standalone output)
Stage 3 (runner):  node:22-alpine → Copy .next/standalone + .next/static + public
                   Non-root user (1001), EXPOSE 3000, CMD ["node", "server.js"]
```

**Build-time args**: `NEXT_PUBLIC_API_URL` (baked into client JS at build time)
**Runtime env**: `HOSTNAME=0.0.0.0`, `PORT=3000`, `NODE_ENV=production`

**Critical**: `NEXT_PUBLIC_*` vars must be set at build time because Next.js inlines them during the build. In Minikube, this means the NodePort URL or Ingress hostname.

#### 2b. Dockerfile.backend

```
Stage 1 (deps):    python:3.13-slim → pip install from pyproject.toml
Stage 2 (runner):  python:3.13-slim → Copy installed packages + app/ code
                   Non-root user (1001), EXPOSE 8000
                   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Runtime env**: All via K8s ConfigMap/Secret (DATABASE_URL, CORS_ORIGINS, etc.)

#### 2c. Dockerfile.mcp

```
Stage 1 (deps):    python:3.13-slim → pip install from pyproject.toml
Stage 2 (runner):  python:3.13-slim → Copy installed packages + mcp_server/ code
                   Non-root user (1001), EXPOSE 8001
                   CMD ["uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Note**: MCP server needs a separate `requirements-mcp.txt` extracted from `pyproject.toml` dependencies relevant to MCP (sqlmodel, asyncpg, mcp, httpx, etc.) to keep the image lean. Alternatively, share the full `pyproject.toml` for simplicity.

**Decision**: Use the full `pyproject.toml` for both backend and MCP images. The extra deps add minimal size and avoid maintenance burden of a separate requirements file.

### 3. Kubernetes Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Minikube Cluster                             │
│                                                                  │
│  ┌──────────────────┐   ┌──────────────────┐                    │
│  │ Frontend Pod      │   │ Backend Pod       │                   │
│  │ (Next.js :3000)   │──▶│ (FastAPI :8000)   │                   │
│  └──────┬───────────┘   └──────┬───────────┘                    │
│         │                      │                                 │
│  NodePort :30080          ClusterIP                              │
│  (external access)        (internal only)                        │
│                                │                                 │
│                          ┌─────▼────────────┐                   │
│                          │ MCP Server Pod    │                   │
│                          │ (FastMCP :8001)   │                   │
│                          └──────────────────┘                   │
│                           ClusterIP                              │
│                           (internal only)                        │
└──────────────────────────────────────────────────────────────────┘
         │                       │                    │
         ▼                       ▼                    ▼
    Developer's            Neon PostgreSQL        OpenAI / OpenRouter
    Browser                (external)             (external)
```

| Service | Type | Port | Target Port | Rationale |
|---------|------|------|-------------|-----------|
| `todo-frontend` | **NodePort** | 30080 | 3000 | Developers access UI from host browser |
| `todo-backend` | **ClusterIP** | 8000 | 8000 | Only frontend (in-cluster) needs to reach it |
| `todo-mcp` | **ClusterIP** | 8001 | 8001 | Only backend (in-cluster) needs to reach it |

**Why NodePort for frontend**: Simplest for Minikube. `minikube service` can open the URL automatically. Ingress is optional and disabled by default in `values.yaml`.

**Why ClusterIP for backend/MCP**: These are internal services. The frontend's Next.js server-side code (proxy, API routes) calls backend at `http://todo-backend:8000` via cluster DNS. No external access needed.

### 4. Helm Chart Structure

```yaml
# chart/Chart.yaml
apiVersion: v2
name: todo-app
description: Hackathon Todo Chatbot - Full Stack Deployment
type: application
version: 0.1.0
appVersion: "1.0.0"
```

**Templates** (one file per resource for clarity):

| Template File | K8s Resource | Purpose |
|---------------|-------------|---------|
| `_helpers.tpl` | — | Name, fullname, labels, selectorLabels helpers |
| `frontend-deployment.yaml` | Deployment | Frontend pod spec with probes + resources |
| `frontend-service.yaml` | Service (NodePort) | Expose frontend to host |
| `backend-deployment.yaml` | Deployment | Backend pod spec with probes + resources |
| `backend-service.yaml` | Service (ClusterIP) | Internal backend access |
| `mcp-deployment.yaml` | Deployment | MCP server pod spec with probes + resources |
| `mcp-service.yaml` | Service (ClusterIP) | Internal MCP access |
| `configmap.yaml` | ConfigMap | Non-sensitive config for all services |
| `secret.yaml` | Secret | Sensitive credentials |
| `ingress.yaml` | Ingress | Optional hostname-based routing |
| `NOTES.txt` | — | Post-install help text |

### 5. ConfigMap and Secret Design

#### ConfigMap (`todo-app-config`)

| Key | Used By | Default Value |
|-----|---------|---------------|
| `LOG_LEVEL` | Backend, MCP | `info` |
| `DEBUG` | Backend | `false` |
| `BETTER_AUTH_URL` | Backend, MCP | `http://todo-app-frontend:3000` |
| `CORS_ORIGINS` | Backend | `http://localhost:30080` |
| `MCP_SERVER_URL` | Backend | `http://todo-app-mcp:8001/mcp` |
| `MCP_SERVER_PORT` | MCP | `8001` |
| `BACKEND_URL` | Frontend | `http://todo-app-backend:8000` |
| `OPENAI_BASE_URL` | Backend | `https://openrouter.ai/api/v1` |

#### Secret (`todo-app-secret`)

| Key | Used By | Source |
|-----|---------|--------|
| `DATABASE_URL` | Backend, MCP | Neon connection string |
| `BETTER_AUTH_SECRET` | Frontend | Random 32-byte base64 |
| `OPENAI_API_KEY` | Backend | OpenAI / OpenRouter API key |
| `FRONTEND_DATABASE_URL` | Frontend | Neon connection string (standard pg format for Better Auth) |

**Design principle**: ConfigMap for anything you'd change without rebuilding. Secret for anything that must never appear in `kubectl describe configmap` output.

### 6. Health Check Configuration

Health endpoints must be added to the application code before K8s probes work:

#### Frontend (Next.js)
- **Probe path**: `/api/health` (new API route returning `{ "status": "ok" }`)
- **Liveness**: `httpGet /api/health :3000` every 30s, 3 failures to restart
- **Readiness**: `httpGet /api/health :3000` every 10s, 3 failures to remove from service

#### Backend (FastAPI)
- **Probe path**: `/health` (new endpoint returning `{ "status": "ok" }`)
- **Liveness**: `httpGet /health :8000` every 30s, 3 failures to restart
- **Readiness**: `httpGet /health :8000` every 10s, check DB connectivity

#### MCP Server (FastMCP)
- **Probe path**: `/health` (new endpoint returning `{ "status": "ok" }`)
- **Liveness**: `httpGet /health :8001` every 30s, 3 failures to restart
- **Readiness**: `httpGet /health :8001` every 10s, check DB connectivity

**Probe timing (all services)**:

```yaml
startupProbe:
  httpGet:
    path: <path>
    port: <port>
  failureThreshold: 30
  periodSeconds: 2      # Up to 60s for initial startup

livenessProbe:
  httpGet:
    path: <path>
    port: <port>
  initialDelaySeconds: 0  # startupProbe handles delay
  periodSeconds: 30
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: <path>
    port: <port>
  initialDelaySeconds: 0
  periodSeconds: 10
  failureThreshold: 3
```

### 7. Resource Limits

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| Frontend | 100m | 500m | 128Mi | 512Mi |
| Backend | 100m | 500m | 128Mi | 512Mi |
| MCP Server | 50m | 250m | 64Mi | 256Mi |

**Total cluster footprint**: 250m CPU request, 320Mi memory request — well within Minikube's 4 CPU / 8GB allocation.

### 8. Security Context (all pods)

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  fsGroup: 1001
containerSecurityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false    # Next.js and Python need /tmp writes
  capabilities:
    drop: ["ALL"]
```

**Note**: `readOnlyRootFilesystem: false` because Next.js writes to `.next/cache` and Python needs writable `/tmp`. A production hardening pass could mount emptyDir at those paths.

### 9. values.yaml Design

```yaml
# Global
global:
  namespace: todo-app
  imagePullPolicy: IfNotPresent    # Use local images in Minikube

# Frontend
frontend:
  enabled: true
  replicaCount: 1
  image:
    repository: todo-frontend
    tag: "latest"
  service:
    type: NodePort
    port: 3000
    nodePort: 30080
  resources:
    requests: { cpu: 100m, memory: 128Mi }
    limits:   { cpu: 500m, memory: 512Mi }
  env:
    NEXT_PUBLIC_API_URL: "http://localhost:30080"

# Backend
backend:
  enabled: true
  replicaCount: 1
  image:
    repository: todo-backend
    tag: "latest"
  service:
    type: ClusterIP
    port: 8000
  resources:
    requests: { cpu: 100m, memory: 128Mi }
    limits:   { cpu: 500m, memory: 512Mi }

# MCP Server
mcp:
  enabled: true
  replicaCount: 1
  image:
    repository: todo-mcp
    tag: "latest"
  service:
    type: ClusterIP
    port: 8001
  resources:
    requests: { cpu: 50m, memory: 64Mi }
    limits:   { cpu: 250m, memory: 256Mi }

# Configuration (non-sensitive → ConfigMap)
config:
  logLevel: "info"
  debug: "false"
  betterAuthUrl: "http://todo-app-frontend:3000"
  corsOrigins: "http://localhost:30080"
  mcpServerUrl: "http://todo-app-mcp:8001/mcp"
  mcpServerPort: "8001"
  backendUrl: "http://todo-app-backend:8000"
  openaiBaseUrl: "https://openrouter.ai/api/v1"

# Secrets (sensitive → K8s Secret, base64-encoded in values or --set)
secrets:
  databaseUrl: ""          # MUST be set via --set or values override
  betterAuthSecret: ""     # MUST be set
  openaiApiKey: ""         # MUST be set
  frontendDatabaseUrl: ""  # MUST be set (standard pg format for Better Auth)

# Ingress (optional, disabled by default)
ingress:
  enabled: false
  className: nginx
  host: todo.local
```

### 10. Development Workflow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│ 1. Setup    │────▶│ 2. Build     │────▶│ 3. Deploy    │────▶│ 4. Test │
│ Minikube    │     │ Images       │     │ Helm Install │     │ Access  │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────┘
```

#### Step 1: Minikube Setup
```bash
# Start cluster with adequate resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Enable required addons
minikube addons enable ingress        # Optional: for hostname routing
minikube addons enable metrics-server  # Optional: for kubectl top

# Point Docker CLI to Minikube's daemon
eval $(minikube docker-env)
```

#### Step 2: Build Images
```bash
# Build all three images (inside Minikube's Docker)
docker build -f Dockerfile.frontend -t todo-frontend:latest ./frontend
docker build -f Dockerfile.backend  -t todo-backend:latest  ./backend
docker build -f Dockerfile.mcp      -t todo-mcp:latest      ./backend
```

#### Step 3: Deploy with Helm
```bash
# First install
helm install todo-app ./chart \
  --namespace todo-app \
  --create-namespace \
  --set secrets.databaseUrl="postgresql://..." \
  --set secrets.frontendDatabaseUrl="postgresql://..." \
  --set secrets.betterAuthSecret="$(openssl rand -base64 32)" \
  --set secrets.openaiApiKey="sk-..."

# Subsequent upgrades
helm upgrade todo-app ./chart \
  --namespace todo-app \
  --reuse-values
```

#### Step 4: Test & Access
```bash
# Check pod status
kubectl get pods -n todo-app

# Get frontend URL
minikube service todo-app-frontend -n todo-app --url

# View logs
kubectl logs -n todo-app -l app.kubernetes.io/component=frontend
kubectl logs -n todo-app -l app.kubernetes.io/component=backend
kubectl logs -n todo-app -l app.kubernetes.io/component=mcp
```

### 11. Minikube Setup Details

**Prerequisites**:
- Docker Desktop or Docker Engine
- Minikube >= 1.33
- Helm >= 3.14
- kubectl >= 1.29

**Recommended Minikube Configuration**:
```bash
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=20g \
  --driver=docker
```

**Required Addons**:
| Addon | Required? | Purpose |
|-------|-----------|---------|
| ingress | Optional | Hostname-based routing (`todo.local`) |
| metrics-server | Optional | `kubectl top pods` resource monitoring |
| dashboard | Optional | Web UI for cluster management |

**Ingress Setup** (optional):
```bash
minikube addons enable ingress
# Add to /etc/hosts: $(minikube ip)  todo.local
# Then set ingress.enabled=true in values.yaml
```

### 12. Troubleshooting Guide

| Symptom | Cause | Fix |
|---------|-------|-----|
| Pod in `ImagePullBackOff` | Image not in Minikube's Docker | Run `eval $(minikube docker-env)` then rebuild images |
| Pod in `CrashLoopBackOff` | App crash on startup (missing env vars) | Check `kubectl logs <pod> -n todo-app` for missing config |
| Pod `Pending` | Insufficient resources | Check `kubectl describe pod` for resource events; increase Minikube CPU/memory |
| Frontend can't reach backend | Wrong service URL in ConfigMap | Verify `BACKEND_URL` matches `<release>-backend:<port>` |
| Backend can't reach MCP | Wrong MCP_SERVER_URL | Verify `MCP_SERVER_URL` matches `http://<release>-mcp:8001/mcp` |
| DB connection refused | Wrong DATABASE_URL in secret | Verify Neon connection string and SSL settings |
| Health check failing | Health endpoint not implemented | Ensure `/health` or `/api/health` routes exist in app code |
| `helm install` fails | Chart validation error | Run `helm lint ./chart` to check for template errors |
| Slow pod startup | Image not cached locally | First build takes time; subsequent builds use Docker layer cache |
| Cannot access NodePort | Minikube networking | Use `minikube service todo-app-frontend -n todo-app --url` |

**Useful Debug Commands**:
```bash
# Pod details and events
kubectl describe pod <pod-name> -n todo-app

# Real-time log streaming
kubectl logs -f <pod-name> -n todo-app

# Exec into container
kubectl exec -it <pod-name> -n todo-app -- /bin/sh

# Port-forward for debugging individual services
kubectl port-forward svc/todo-app-backend 8000:8000 -n todo-app

# Check resource usage
kubectl top pods -n todo-app

# Helm release status
helm status todo-app -n todo-app
helm history todo-app -n todo-app
```

---

## Implementation Prerequisites

Before K8s deployment, these code changes are required:

1. **Add `output: "standalone"` to `frontend/next.config.ts`** — required for Docker standalone build
2. **Add `GET /health` endpoint to `backend/app/main.py`** — required for K8s probes
3. **Add `GET /health` endpoint to `backend/mcp_server/server.py`** — required for K8s probes
4. **Add `GET /api/health` route to `frontend/src/app/api/health/route.ts`** — required for K8s probes

---

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| `NEXT_PUBLIC_*` vars baked at build time | Frontend image must be rebuilt when backend URL changes | Document clearly; provide build script with configurable arg |
| Neon DB unreachable from Minikube | All pods fail readiness checks | Readiness probes remove unhealthy pods; frontend shows error; document firewall/DNS requirements |
| Minikube resource exhaustion | Pods stuck in Pending | Set conservative resource limits; document minimum cluster requirements |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `/health` endpoints skip JWT auth (Security §1) | K8s liveness/readiness probes cannot carry Authorization headers | No alternative — all K8s health probes are unauthenticated by design |

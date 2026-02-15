# Tasks: Local Kubernetes Deployment

**Input**: Design documents from `/specs/003-kubernetes-local/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by implementation phase mapping to user stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Prerequisites (Application Code Changes)

**Purpose**: Add health endpoints and configure Next.js for Docker — required before any containerization work.

- [x] T001 [P] Add `output: "standalone"` to Next.js config in `frontend/next.config.ts`. Keep existing `serverExternalPackages: ["better-auth"]`. This enables the minimal standalone production build needed for Docker. See research.md R1.

- [x] T002 [P] Add health check API route for frontend at `frontend/src/app/api/health/route.ts`. Create a Next.js App Router API route that returns `{ "status": "ok" }` with 200 status. This is a simple GET handler using `NextResponse.json()`.

- [x] T003 [P] Add `/health` endpoint to backend FastAPI app in `backend/app/main.py`. Add a simple `@app.get("/health")` endpoint returning `{"status": "ok"}`. Place it after the router includes. No authentication required — K8s probes cannot carry auth headers (documented exception in plan.md Complexity Tracking). Simple HTTP 200 is sufficient for both liveness and readiness; no DB connectivity check needed for local dev.

- [x] T004 [P] Add `/health` endpoint to MCP server in `backend/mcp_server/server.py`. The current `app = mcp.streamable_http_app()` returns a Starlette ASGI app. Replace this with a Starlette `Router` (or `Starlette` app) that mounts the MCP app at `/mcp` and adds a plain `Route("/health", ...)` returning JSON `{"status": "ok"}` with `JSONResponse`. No auth required (same exception as T003). Simple HTTP 200, no DB check.

**Checkpoint**: All services now have health endpoints. Verify locally:
- `curl http://localhost:3000/api/health` → `{"status":"ok"}`
- `curl http://localhost:8000/health` → `{"status":"ok"}`
- `curl http://localhost:8001/health` → `{"status":"ok"}`

---

## Phase 2: Docker Images (Containerization)

**Purpose**: Create Dockerfiles for all three services using the docker-containerization skill templates.

**⚠️ CRITICAL**: Depends on Phase 1 completion (health endpoints + standalone config).

- [x] T005 Create `.dockerignore` at repository root. Exclude: `node_modules`, `.next`, `__pycache__`, `.env*`, `.git`, `*.md`, `specs/`, `history/`, `.specify/`, `.claude/`, `chart/`, `scripts/`, `*.pyc`, `.pytest_cache`, `.mypy_cache`, `venv/`, `.venv/`. Reference `.claude/skills/docker-containerization/templates/dockerignore.template`.

- [x] T006 [P] Create `Dockerfile.frontend` at repository root for the Next.js frontend. Use multi-stage build per plan.md section 2a and `.claude/skills/docker-containerization/templates/dockerfile-nextjs.template`:
  - **Build context**: `./frontend` — all COPY paths are relative to `frontend/`, so use `package.json` not `frontend/package.json`
  - **Stage 1 (deps)**: `FROM node:22-alpine AS deps` → `WORKDIR /app` → Copy `package.json` and `package-lock.json` → `npm ci`
  - **Stage 2 (build)**: `FROM node:22-alpine AS build` → `WORKDIR /app` → Copy `node_modules` from deps → Copy all source (`.`) → `ARG NEXT_PUBLIC_API_URL=http://localhost:30080` → `npm run build`
  - **Stage 3 (runner)**: `FROM node:22-alpine AS runner` → `WORKDIR /app` → Create non-root user (UID 1001) → Copy `.next/standalone/`, `.next/static/`, `public/` from build stage → `ENV HOSTNAME=0.0.0.0 PORT=3000 NODE_ENV=production` → `EXPOSE 3000` → `USER 1001` → `CMD ["node", "server.js"]`
  - **Build command**: `docker build -f Dockerfile.frontend -t todo-frontend:latest ./frontend`
  - **HEALTHCHECK**: `wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1`
  - **Size target**: < 300MB

- [x] T007 [P] Create `Dockerfile.backend` at repository root for the FastAPI backend. Use multi-stage build per plan.md section 2b and `.claude/skills/docker-containerization/templates/dockerfile-fastapi.template`:
  - **Stage 1 (deps)**: `FROM python:3.13-slim AS deps` → Copy `backend/pyproject.toml` → `pip install --no-cache-dir .` into a virtual env or `--prefix=/install`
  - **Stage 2 (runner)**: `FROM python:3.13-slim AS runner` → Create non-root user (UID 1001) → Copy installed packages from deps stage → Copy `backend/app/` source code → Copy `backend/alembic/` and `backend/alembic.ini` for migrations → `ENV PYTHONUNBUFFERED=1` → `EXPOSE 8000` → `USER 1001` → `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`
  - **Build context**: `./backend`
  - **HEALTHCHECK**: `curl -f http://localhost:8000/health || exit 1` (install curl in deps stage) OR use python urllib
  - **Size target**: < 400MB

- [x] T008 [P] Create `Dockerfile.mcp` at repository root for the MCP server. Use multi-stage build per plan.md section 2c:
  - **Stage 1 (deps)**: `FROM python:3.13-slim AS deps` → Copy `backend/pyproject.toml` → `pip install --no-cache-dir .` (shares same deps as backend)
  - **Stage 2 (runner)**: `FROM python:3.13-slim AS runner` → Create non-root user (UID 1001) → Copy installed packages from deps stage → Copy `backend/mcp_server/` source code only → `ENV PYTHONUNBUFFERED=1` → `EXPOSE 8001` → `USER 1001` → `CMD ["uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8001"]`
  - **Build context**: `./backend`
  - **HEALTHCHECK**: same approach as backend
  - **Size target**: < 400MB

**Checkpoint**: Images can be built locally:
```bash
docker build -f Dockerfile.frontend -t todo-frontend:latest ./frontend
docker build -f Dockerfile.backend -t todo-backend:latest ./backend
docker build -f Dockerfile.mcp -t todo-mcp:latest ./backend
```

---

## Phase 3: Helm Chart — User Story 1 (One-Command Stack Deployment, P1) 🎯 MVP

**Goal**: Deploy all three services to Minikube with a single `helm install` command. All pods reach Running state within 120s.

**Independent Test**: `helm install todo-app ./chart --namespace todo-app --create-namespace --set secrets.databaseUrl=... --set secrets.betterAuthSecret=... --set secrets.openaiApiKey=... --set secrets.frontendDatabaseUrl=...` → `kubectl get pods -n todo-app` shows 3 Running pods.

### Chart Scaffolding

- [x] T009 Create Helm chart scaffolding. Create the following files per plan.md section 4 and `.claude/skills/kubernetes-helm-charts/templates/helm-chart-structure.template`:
  - `chart/Chart.yaml` — apiVersion v2, name `todo-app`, version `0.1.0`, appVersion `1.0.0`, description "Hackathon Todo Chatbot - Full Stack Deployment"
  - `chart/.helmignore` — standard patterns (`.git`, `*.swp`, `.DS_Store`, etc.)

- [x] T010 [US1] Create `chart/templates/_helpers.tpl` with Helm helper templates. Reference `.claude/skills/kubernetes-helm-charts/examples/fullstack-helm-chart-example/templates/_helpers.tpl`. Include helpers for:
  - `todo-app.name` — chart name
  - `todo-app.fullname` — release-prefixed name
  - `todo-app.chart` — chart name + version
  - `todo-app.labels` — standard K8s labels (helm.sh/chart, app.kubernetes.io/name, instance, managed-by)
  - `todo-app.selectorLabels` — just name + instance for selectors
  - Component-specific helpers: `todo-app.frontend.fullname`, `todo-app.backend.fullname`, `todo-app.mcp.fullname` appending component suffix

- [x] T011 [US1] Create `chart/values.yaml` with all default values per plan.md section 9. Include all sections:
  - `global.imagePullPolicy: IfNotPresent`
  - `frontend.*` (image repo/tag, replicaCount, service type NodePort/port/nodePort, resources, env)
  - `backend.*` (image repo/tag, replicaCount, service type ClusterIP/port, resources)
  - `mcp.*` (image repo/tag, replicaCount, service type ClusterIP/port, resources)
  - `config.*` (logLevel, debug, betterAuthUrl, corsOrigins, mcpServerUrl, mcpServerPort, backendUrl, openaiBaseUrl)
  - `secrets.*` (databaseUrl, betterAuthSecret, openaiApiKey, frontendDatabaseUrl — all empty string defaults)
  - `ingress.*` (enabled: false, className: nginx, host: todo.local)
  - Resource limits per plan.md section 7

### Kubernetes Resources (ConfigMap, Secret, Deployments, Services)

- [x] T012 [P] [US1] Create `chart/templates/configmap.yaml`. Template a ConfigMap named `{{ include "todo-app.fullname" . }}-config` with data from `.Values.config.*` keys mapped to env var names: `LOG_LEVEL`, `DEBUG`, `BETTER_AUTH_URL`, `CORS_ORIGINS`, `MCP_SERVER_URL`, `MCP_SERVER_PORT`, `BACKEND_URL`, `OPENAI_BASE_URL`. Apply standard labels. Reference plan.md section 5.

- [x] T013 [P] [US1] Create `chart/templates/secret.yaml`. Template a Secret named `{{ include "todo-app.fullname" . }}-secret` of type Opaque. Data keys: `DATABASE_URL`, `BETTER_AUTH_SECRET`, `OPENAI_API_KEY`, `FRONTEND_DATABASE_URL` using `{{ .Values.secrets.<key> | b64enc }}`. Apply standard labels. Reference plan.md section 5.

- [x] T014 [P] [US1] Create `chart/templates/frontend-deployment.yaml`. Template a Deployment for the frontend:
  - Name: `{{ include "todo-app.frontend.fullname" . }}`
  - Labels: standard + `app.kubernetes.io/component: frontend`
  - Selector: `app.kubernetes.io/name: {{ include "todo-app.name" . }}, component: frontend`
  - Replicas: `{{ .Values.frontend.replicaCount }}`
  - Container: image `{{ .Values.frontend.image.repository }}:{{ .Values.frontend.image.tag }}`, port 3000
  - `envFrom`: ConfigMap ref + Secret ref (both from T012/T013)
  - Resources from `{{ .Values.frontend.resources }}`
  - Security context per plan.md section 8 (runAsNonRoot, runAsUser 1001, drop ALL capabilities)
  - Health probes per plan.md section 6: startupProbe, livenessProbe, readinessProbe all on `/api/health` port 3000
  - `imagePullPolicy: {{ .Values.global.imagePullPolicy }}`

- [x] T015 [P] [US1] Create `chart/templates/backend-deployment.yaml`. Template a Deployment for the backend:
  - Name: `{{ include "todo-app.backend.fullname" . }}`
  - Labels: standard + `app.kubernetes.io/component: backend`
  - Same pattern as frontend but: port 8000, probes on `/health` port 8000
  - Resources from `{{ .Values.backend.resources }}`

- [x] T016 [P] [US1] Create `chart/templates/mcp-deployment.yaml`. Template a Deployment for the MCP server:
  - Name: `{{ include "todo-app.mcp.fullname" . }}`
  - Labels: standard + `app.kubernetes.io/component: mcp`
  - Same pattern as backend but: port 8001, probes on `/health` port 8001
  - Resources from `{{ .Values.mcp.resources }}`

- [x] T017 [P] [US1] Create `chart/templates/frontend-service.yaml`. Template a Service for the frontend:
  - Name: `{{ include "todo-app.frontend.fullname" . }}`
  - Type: `{{ .Values.frontend.service.type }}` (default NodePort)
  - Port: `{{ .Values.frontend.service.port }}` (3000)
  - NodePort: `{{ .Values.frontend.service.nodePort }}` (30080) — only if type is NodePort
  - Selector: matching frontend deployment labels

- [x] T018 [P] [US1] Create `chart/templates/backend-service.yaml`. Template a Service for the backend:
  - Name: `{{ include "todo-app.backend.fullname" . }}`
  - Type: `{{ .Values.backend.service.type }}` (default ClusterIP)
  - Port: `{{ .Values.backend.service.port }}` (8000)
  - Selector: matching backend deployment labels

- [x] T019 [P] [US1] Create `chart/templates/mcp-service.yaml`. Template a Service for the MCP server:
  - Name: `{{ include "todo-app.mcp.fullname" . }}`
  - Type: `{{ .Values.mcp.service.type }}` (default ClusterIP)
  - Port: `{{ .Values.mcp.service.port }}` (8001)
  - Selector: matching MCP deployment labels

- [x] T020 [US1] Create `chart/templates/NOTES.txt` with post-install instructions. Show the user:
  - How to check pod status: `kubectl get pods -n {{ .Release.Namespace }}`
  - How to access the frontend: `minikube service {{ include "todo-app.frontend.fullname" . }} -n {{ .Release.Namespace }} --url`
  - How to view logs per service
  - How to upgrade: `helm upgrade`
  - How to uninstall: `helm uninstall`

**Checkpoint — US1 Complete**: `helm install todo-app ./chart --namespace todo-app --create-namespace --set secrets.databaseUrl=... ...` → all 3 pods Running. This validates FR-001 through FR-007, FR-010, FR-011, FR-012, FR-013, FR-014, SC-001.

---

## Phase 4: User Story 2 — Access Frontend Locally (P1)

**Goal**: Developer can access the Todo Chatbot frontend through a browser at NodePort URL and use the full app.

**Independent Test**: Open browser to `http://localhost:30080` (or `minikube service` URL) → see Todo Chatbot UI → create/view/update/delete a todo.

- [x] T021 [P] [US2] Create `chart/templates/ingress.yaml` with optional Ingress resource. Wrap entire template in `{{- if .Values.ingress.enabled }}`. Configure:
  - IngressClassName: `{{ .Values.ingress.className }}`
  - Host: `{{ .Values.ingress.host }}`
  - Path `/` → service `{{ include "todo-app.frontend.fullname" . }}` port `{{ .Values.frontend.service.port }}`
  - Standard annotations for nginx ingress controller
  - Reference `.claude/skills/kubernetes-helm-charts/templates/ingress.yaml.template`

**Checkpoint — US2 Complete**: Frontend accessible via NodePort. Ingress available when enabled. Validates FR-005, SC-002.

---

## Phase 5: User Story 3 — Health Monitoring and Debugging (P2)

**Goal**: Developer can verify pod health via `kubectl get pods` and view logs for troubleshooting.

**Independent Test**: `kubectl get pods -n todo-app` shows all pods `1/1 Running`. `kubectl logs -l app.kubernetes.io/component=backend -n todo-app` shows application logs.

- [x] T022 [US3] Verify health probe configuration across all three deployment templates. Ensure:
  - startupProbe: `failureThreshold: 30`, `periodSeconds: 2` (allows 60s startup)
  - livenessProbe: `periodSeconds: 30`, `failureThreshold: 3`
  - readinessProbe: `periodSeconds: 10`, `failureThreshold: 3`
  - Correct paths: `/api/health` for frontend, `/health` for backend and MCP
  - Cross-reference with health endpoints from T002, T003, T004

**Checkpoint — US3 Complete**: Pods self-heal on failure. Logs accessible. Validates FR-011, SC-005.

---

## Phase 6: User Story 4 — Configuration and Secrets Management (P2)

**Goal**: Non-sensitive config in ConfigMap, secrets in K8s Secret. Changes applied via rollout restart.

**Independent Test**: `kubectl describe configmap -n todo-app` shows non-sensitive config. `kubectl get secret -n todo-app` shows secret exists. Change a ConfigMap value → `kubectl rollout restart` → pod picks up new value.

- [x] T023 [US4] Verify ConfigMap and Secret separation. Review T012 and T013 outputs to confirm:
  - No secrets (DATABASE_URL, API keys, auth secrets) appear in ConfigMap
  - All `config.*` values map correctly to env var names
  - All `secrets.*` values are base64-encoded in the Secret
  - Both resources are referenced via `envFrom` in all three deployments
  - Reference plan.md section 5 tables for expected key mappings

**Checkpoint — US4 Complete**: Config/secrets properly separated. Validates FR-008, FR-009, SC-003.

---

## Phase 7: User Story 5 — Helm Upgrade and Rollback (P3)

**Goal**: `helm upgrade` updates pods with new config/images. `helm rollback` restores previous version.

**Independent Test**: `helm upgrade todo-app ./chart --set config.logLevel=debug` → pods restart with new config. `helm rollback todo-app 1` → previous config restored.

- [x] T024 [US5] Verify rolling update strategy in all deployment templates. Ensure:
  - `strategy.type: RollingUpdate` with `maxSurge: 1` and `maxUnavailable: 0` for zero-downtime upgrades
  - This allows `helm upgrade` to update pods without downtime
  - Validates FR-014, SC-003, SC-004

**Checkpoint — US5 Complete**: Upgrade and rollback work. Validates SC-003, SC-004.

---

## Phase 8: Developer Workflow & Scripts

**Purpose**: One-command setup script and documentation for the full build-deploy-test workflow.

- [x] T025 Create `scripts/minikube-setup.sh` at repository root. The script should:
  - Check prerequisites (docker, minikube, helm, kubectl) and print errors for missing ones
  - Start Minikube: `minikube start --cpus=4 --memory=8192 --driver=docker`
  - Point Docker to Minikube: `eval $(minikube docker-env)`
  - Build all 3 images: `docker build -f Dockerfile.frontend/backend/mcp ...`
  - Accept secrets as env vars or arguments (`DATABASE_URL`, `BETTER_AUTH_SECRET`, `OPENAI_API_KEY`, `FRONTEND_DATABASE_URL`)
  - Run `helm install` with the secrets
  - Wait for pods to be ready: `kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-app -n todo-app --timeout=120s`
  - Print the frontend URL via `minikube service`
  - Make the script executable (`chmod +x`)
  - Validates FR-015, SC-006

- [x] T026 Add `chart/.helmignore` entries for non-chart files. Ensure patterns exclude: `*.md`, `.git`, `.gitignore`, `tests/`, `*.swp`, `.DS_Store`, `.env*`.

**Checkpoint**: Developer can run `scripts/minikube-setup.sh` for end-to-end setup. Validates SC-006 (< 10 min from fresh cluster).

---

## Phase 9: Polish & Validation

**Purpose**: Final validation, lint checks, and documentation alignment.

- [x] T027 [P] Run `helm lint ./chart` to validate chart syntax and fix any errors. Run `helm template todo-app ./chart` to verify rendered manifests look correct. Fix any template rendering issues.

- [x] T028 [P] Verify all `.dockerignore` exclusions are correct. Ensure `node_modules`, `.git`, `specs/`, `history/`, `.specify/`, `.claude/` are excluded from build contexts. Test with `docker build --no-cache` to confirm clean builds.

- [x] T029 Update `specs/003-kubernetes-local/quickstart.md` to match final implementation. Ensure all commands, file paths, and instructions are accurate against the actual generated files.

**Checkpoint — All Stories Complete**: Full stack deploys to Minikube via Helm. Frontend accessible. Health probes working. Config/secrets separated. Upgrade/rollback functional. Developer script automates everything.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Prerequisites ──────────────────────────────── (no deps, start immediately)
  T001, T002, T003, T004 [all parallel]
         │
         ▼
Phase 2: Docker Images ──────────────────────────────── (depends on Phase 1)
  T005 first, then T006, T007, T008 [parallel]
         │
         ▼
Phase 3: Helm Chart / US1 ───────────────────────────── (depends on Phase 2)
  T009 → T010, T011 → T012-T019 [parallel] → T020
         │
         ├──▶ Phase 4: US2 (T021) ───────────────────── (depends on Phase 3)
         ├──▶ Phase 5: US3 (T022) ───────────────────── (depends on Phase 3)
         ├──▶ Phase 6: US4 (T023) ───────────────────── (depends on Phase 3)
         └──▶ Phase 7: US5 (T024) ───────────────────── (depends on Phase 3)
                    │
                    ▼
Phase 8: Scripts (T025, T026) ───────────────────────── (depends on Phase 3)
                    │
                    ▼
Phase 9: Validation (T027, T028, T029) ──────────────── (depends on all above)
```

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 1 + 2 — BLOCKS all other stories
- **US2 (P1)**: Depends on US1 (needs deployed stack with NodePort service)
- **US3 (P2)**: Depends on US1 (needs deployed pods with health probes)
- **US4 (P2)**: Depends on US1 (needs ConfigMap and Secret created)
- **US5 (P3)**: Depends on US1 (needs initial deployment for upgrade/rollback)

### Parallel Opportunities

```
# Phase 1 — all 4 tasks in parallel:
T001 ┐
T002 ├── All modify different files
T003 │
T004 ┘

# Phase 2 — 3 Dockerfiles in parallel (after T005):
T006 ┐
T007 ├── All different Dockerfiles
T008 ┘

# Phase 3 — most templates in parallel (after T009-T011):
T012 ┐
T013 │
T014 │
T015 ├── All different template files
T016 │
T017 │
T018 │
T019 ┘

# Phases 4-7 — all in parallel (after Phase 3):
T021 ┐
T022 ├── Independent user stories
T023 │
T024 ┘
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Prerequisites (T001-T004, ~10 min)
2. Complete Phase 2: Docker Images (T005-T008, ~30 min)
3. Complete Phase 3: Helm Chart core (T009-T020, ~45 min)
4. **STOP and VALIDATE**: `helm install` → 3 pods Running
5. This delivers a working deployment — core value delivered

### Incremental Delivery

1. **MVP**: Phases 1-3 → Stack deploys successfully
2. **+US2**: Phase 4 → Frontend accessible via browser
3. **+US3**: Phase 5 → Health monitoring verified
4. **+US4**: Phase 6 → Config/secrets management verified
5. **+US5**: Phase 7 → Upgrade/rollback capability
6. **Polish**: Phases 8-9 → Developer script + validation

---

## Notes

- Total tasks: **29** (T001-T029)
- Tasks per phase: Prerequisites(4), Docker(4), Helm/US1(12), US2(1), US3(1), US4(1), US5(1), Scripts(2), Validation(3)
- Parallel opportunities: 4 in Phase 1, 3 in Phase 2, 8 in Phase 3, 4 across Phases 4-7
- All Dockerfiles reference skill templates in `.claude/skills/docker-containerization/templates/`
- All K8s templates reference skill templates in `.claude/skills/kubernetes-helm-charts/templates/`
- No tests included (not requested in spec)
- Commit after each phase completion

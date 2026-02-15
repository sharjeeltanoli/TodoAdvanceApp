# Research: Local Kubernetes Deployment

**Feature**: 003-kubernetes-local | **Date**: 2026-02-15

## Research Tasks & Findings

### R1: Next.js Standalone Output for Docker

**Decision**: Enable `output: "standalone"` in `next.config.ts`
**Rationale**: Next.js standalone mode copies only the necessary files for production, resulting in a minimal Docker image (~100MB vs ~1GB with full `node_modules`). The standalone output includes a `server.js` that can be run with `node server.js` without needing the full framework.
**Alternatives considered**:
- Full `node_modules` in image: Rejected — 3-5x larger image, includes dev dependencies
- Custom server (Express): Rejected — unnecessary complexity; standalone handles this

**Implementation**: Add to `frontend/next.config.ts`:
```ts
const nextConfig: NextConfig = {
  output: "standalone",
  serverExternalPackages: ["better-auth"],
};
```

### R2: Python Base Image Selection

**Decision**: Use `python:3.13-slim` (Debian-based)
**Rationale**: `asyncpg` and `greenlet` require compilation against glibc. Alpine uses musl libc which causes build failures or runtime issues with these libraries. `slim` is ~150MB vs Alpine's ~50MB but avoids all compatibility issues.
**Alternatives considered**:
- `python:3.13-alpine`: Rejected — musl libc issues with asyncpg, greenlet, and other C-extension packages
- `python:3.13`: Rejected — ~900MB, unnecessarily large with full Debian

### R3: Frontend NEXT_PUBLIC_* Environment Variables in Docker

**Decision**: Pass `NEXT_PUBLIC_API_URL` as a Docker build arg
**Rationale**: Next.js inlines `NEXT_PUBLIC_*` variables at build time into the JavaScript bundle. They cannot be changed at runtime. For Minikube, the value will be `http://localhost:30080` (the NodePort URL).
**Alternatives considered**:
- Runtime env replacement script: Rejected — adds complexity; build arg is sufficient for local dev
- Window.__ENV__ injection: Rejected — requires custom server setup

### R4: MCP Server Deployment Strategy

**Decision**: Deploy as a separate pod with its own Dockerfile and Service
**Rationale**: The MCP server is independently scalable, has its own port (8001), and the spec explicitly lists it as a separate deployment. It shares the `backend/` build context but only runs the `mcp_server` module.
**Alternatives considered**:
- Co-located with backend in same pod (sidecar): Rejected — spec requires separate deployments; independent lifecycle management
- Same Docker image with different CMD: Viable but rejected — cleaner separation with dedicated Dockerfile

### R5: Health Endpoint Implementation

**Decision**: Add minimal `/health` (backend, MCP) and `/api/health` (frontend) endpoints
**Rationale**: Kubernetes liveness and readiness probes require HTTP endpoints. Neither service currently has health endpoints. The endpoints should return `{"status": "ok"}` with a 200 status code. Readiness probes for backend/MCP could additionally check DB connectivity, but for local dev, a simple HTTP 200 is sufficient.
**Alternatives considered**:
- TCP socket probe: Rejected — doesn't verify the application is actually handling requests
- Exec probe (curl): Rejected — requires curl in the container; HTTP probe is simpler

### R6: Service Exposure Strategy (NodePort vs LoadBalancer vs Ingress)

**Decision**: NodePort for frontend (port 30080), ClusterIP for backend and MCP
**Rationale**: NodePort is the simplest way to expose a service from Minikube to the host. LoadBalancer requires `minikube tunnel` which adds a running process. Ingress requires the addon and `/etc/hosts` editing. NodePort works immediately with `minikube service --url`.
**Alternatives considered**:
- LoadBalancer for frontend: Viable but requires `minikube tunnel` running in a separate terminal
- Ingress for all: More production-like but adds setup steps; offered as optional in values.yaml

### R7: Secret Management in Helm

**Decision**: Secrets passed via `--set` flags or a local values override file (not committed)
**Rationale**: Helm's `values.yaml` is committed to git, so secrets must not be in default values. Using `--set` or a local `values-secrets.yaml` (gitignored) keeps secrets out of version control.
**Alternatives considered**:
- External Secrets Operator: Rejected — overkill for local development
- Sealed Secrets: Rejected — requires additional controller; not needed for Minikube
- .env file mounting: Rejected — Helm's native Secret resources are the standard K8s pattern

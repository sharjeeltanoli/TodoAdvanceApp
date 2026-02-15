# Feature Specification: Local Kubernetes Deployment

**Feature Branch**: `003-kubernetes-local`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "Deploy Todo Chatbot on Minikube with Helm Charts"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-Command Stack Deployment (Priority: P1)

As a developer, I can deploy the entire Todo Chatbot stack (frontend, backend API, and MCP server) to a local Minikube cluster using a single Helm install command, so that I can run the full application in a production-like environment on my machine.

**Why this priority**: This is the core value proposition — without deployment, nothing else works. A single-command deployment reduces friction and makes local K8s development practical.

**Independent Test**: Can be fully tested by running `helm install todo-app ./chart --namespace todo-app --create-namespace` and verifying all three pods reach Running state.

**Acceptance Scenarios**:

1. **Given** Minikube is running and container images are built, **When** I run the Helm install command, **Then** all three deployments (frontend, backend, MCP server) reach Ready state within 120 seconds.
2. **Given** a fresh Minikube cluster with no prior deployments, **When** I run the install command with `--create-namespace`, **Then** the namespace is created and all resources are provisioned without errors.
3. **Given** an existing deployment, **When** I run `helm upgrade` with updated image tags, **Then** pods are replaced via rolling update with zero downtime.

---

### User Story 2 - Access Frontend Locally (Priority: P1)

As a developer, I can access the Todo Chatbot frontend through my browser at a predictable local URL, so that I can interact with the application as an end user would.

**Why this priority**: Developers need to verify the UI is working correctly. Without accessible services, the deployment cannot be validated end-to-end.

**Independent Test**: Can be tested by opening a browser to the exposed NodePort URL and interacting with the Todo Chatbot UI.

**Acceptance Scenarios**:

1. **Given** the stack is deployed, **When** I navigate to the frontend NodePort URL, **Then** the Todo Chatbot UI loads successfully.
2. **Given** the frontend is running, **When** I create a todo item through the UI, **Then** the request routes through the backend and the item is persisted.
3. **Given** Minikube ingress addon is enabled, **When** I configure the Ingress resource, **Then** I can access the app via a hostname (e.g., `todo.local`) without specifying a port.

---

### User Story 3 - Health Monitoring and Debugging (Priority: P2)

As a developer, I can verify that all pods are healthy and view logs for any service, so that I can quickly identify and troubleshoot issues in the local cluster.

**Why this priority**: Debugging is essential for developer productivity. Without observability, developers cannot diagnose deployment or runtime issues.

**Independent Test**: Can be tested by running `kubectl get pods` to see health status and `kubectl logs` to view service output.

**Acceptance Scenarios**:

1. **Given** the stack is deployed, **When** I run `kubectl get pods -n todo-app`, **Then** all pods show Running status with all containers ready (e.g., 1/1).
2. **Given** a pod is running, **When** I run `kubectl logs <pod> -n todo-app`, **Then** I see application logs from the container.
3. **Given** a pod fails its health check, **When** Kubernetes restarts it, **Then** the pod recovers automatically and the service remains available via other replicas.

---

### User Story 4 - Configuration and Secrets Management (Priority: P2)

As a developer, I can manage application configuration and sensitive credentials separately from code, so that settings can be changed without rebuilding images and secrets are not exposed in version control.

**Why this priority**: Proper configuration management is a prerequisite for production-like deployments and prevents credential leaks.

**Independent Test**: Can be tested by modifying a ConfigMap value, performing a rollout restart, and verifying the pod picks up the new value.

**Acceptance Scenarios**:

1. **Given** configuration values are defined in `values.yaml`, **When** I deploy with Helm, **Then** ConfigMaps are created with the correct non-sensitive values (log level, API URLs, feature flags).
2. **Given** secrets are defined in the values file, **When** I deploy with Helm, **Then** Kubernetes Secrets are created for DATABASE_URL, API keys, and auth secrets.
3. **Given** I update a ConfigMap value, **When** I perform a rollout restart, **Then** pods pick up the new configuration without redeployment.

---

### User Story 5 - Helm Upgrade and Rollback (Priority: P3)

As a developer, I can upgrade the deployment with new configuration or image versions, and roll back to a previous release if something goes wrong, so that I can iterate safely.

**Why this priority**: Iterative development requires safe upgrade and rollback capability, but this is secondary to basic deployment.

**Independent Test**: Can be tested by running `helm upgrade`, verifying new pods deploy, then running `helm rollback` and verifying previous version is restored.

**Acceptance Scenarios**:

1. **Given** version 1.0.0 is deployed, **When** I run `helm upgrade` with tag 1.1.0, **Then** pods are updated via rolling update and the new version serves traffic.
2. **Given** an upgrade has been performed, **When** I run `helm rollback todo-app 1`, **Then** the previous version is restored and all pods return to healthy state.

---

### Edge Cases

- What happens when Minikube runs out of allocated CPU or memory? Pods should enter Pending state with clear resource-related error messages; ResourceQuota prevents silent failures.
- How does the system handle the external Neon database being unreachable? Backend pods should fail readiness checks and be removed from service endpoints; the frontend should display a user-friendly error.
- What happens when a container image is not available in the local Docker cache? Pods enter ImagePullBackOff state with a clear error; documentation guides the developer to build images into Minikube's Docker daemon.
- What happens when Minikube is stopped and restarted? Deployments should resume automatically once the cluster is back; persistent data in external Neon is unaffected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST containerize the Next.js frontend into a production-ready Docker image with multi-stage build.
- **FR-002**: System MUST containerize the FastAPI backend (including API routes) into a production-ready Docker image.
- **FR-003**: System MUST containerize the MCP server into a production-ready Docker image, either standalone or as part of the backend image.
- **FR-004**: System MUST provide a Helm chart that deploys all three services (frontend, backend, MCP server) with a single `helm install` command.
- **FR-005**: System MUST expose the frontend via a Kubernetes Service accessible from the developer's host machine (NodePort or Ingress).
- **FR-006**: System MUST expose the backend API via a Kubernetes Service so the frontend can communicate with it within the cluster.
- **FR-007**: System MUST expose the MCP server via a Kubernetes Service so the backend can communicate with it within the cluster.
- **FR-008**: System MUST store non-sensitive configuration (log level, API base URLs, feature flags) in ConfigMaps.
- **FR-009**: System MUST store sensitive configuration (DATABASE_URL, OPENAI_API_KEY, BETTER_AUTH_SECRET) in Kubernetes Secrets.
- **FR-010**: System MUST define resource requests and limits for all containers to prevent resource contention.
- **FR-011**: System MUST configure liveness and readiness probes for all deployments to enable automatic health monitoring and recovery.
- **FR-012**: System MUST use the external Neon PostgreSQL database (no in-cluster database required) to avoid data management complexity in local development.
- **FR-013**: System MUST provide a `values.yaml` with sensible defaults for local Minikube development.
- **FR-014**: System MUST support `helm upgrade` for iterating on configuration and image versions without full redeployment.
- **FR-015**: System MUST include a developer setup script or documented steps to initialize Minikube, build images, and deploy the stack.

### Non-Functional Requirements

- **NFR-001**: All pods MUST reach Running state within 120 seconds of deployment on a standard Minikube cluster (4 CPU, 8GB RAM).
- **NFR-002**: Container images MUST be built using multi-stage Docker builds to minimize image size (frontend < 500MB, backend < 500MB).
- **NFR-003**: Helm chart MUST follow standard conventions (labels, selectors, _helpers.tpl, NOTES.txt).
- **NFR-004**: All containers MUST run as non-root users with minimal capabilities.

### Key Entities

- **Deployment (Frontend)**: Runs the Next.js application container; serves the web UI; connects to backend API service.
- **Deployment (Backend API)**: Runs the FastAPI application container; exposes REST endpoints; connects to external Neon database and internal MCP server.
- **Deployment (MCP Server)**: Runs the MCP server container; provides AI tool capabilities to the backend; connects to external Neon database and AI provider APIs.
- **Helm Chart**: Packages all Kubernetes resources (Deployments, Services, ConfigMaps, Secrets, optional Ingress) into a single installable unit with parameterized values.
- **ConfigMap**: Holds non-sensitive runtime configuration shared across pods.
- **Secret**: Holds sensitive credentials (database URL, API keys, auth secrets) injected as environment variables.

## Scope

### In Scope

- Dockerfiles for frontend, backend, and MCP server
- Helm chart with deployments, services, configmaps, secrets
- Minikube-specific configuration and setup documentation
- NodePort service exposure for local access
- Optional Ingress resource for hostname-based routing
- Developer workflow documentation (build, deploy, upgrade, debug)

### Out of Scope

- Cloud Kubernetes deployment (DigitalOcean, Azure, GCP) — deferred to Phase 5
- CI/CD pipeline integration
- Horizontal Pod Autoscaling (not needed for local development)
- In-cluster database deployment (using external Neon)
- TLS/SSL certificates for local development
- kubectl-ai and kagent AI-assisted operations (optional enhancement, not required for MVP)
- Production-grade monitoring (Prometheus, Grafana)

## Assumptions

- Minikube is installed and configured with at least 4 CPUs and 8GB RAM
- Docker is installed and available on the developer's machine
- The developer has access to the Neon PostgreSQL database URL
- Container images will be built directly into Minikube's Docker daemon (via `eval $(minikube docker-env)`) to avoid needing a remote registry
- The existing Docker Containerization and Kubernetes/Helm Charts skills provide template patterns for implementation
- Helm v3 is installed on the developer's machine
- The MCP server can be deployed as a separate pod with its own service, or co-located with the backend if tightly coupled

## Dependencies

- Phase 1 (001-todo-crud): Frontend and backend application code must be functional
- Phase 2 (002-ai-chatbot): MCP server and chatbot integration must be functional
- Docker Containerization skill: Dockerfile templates for Next.js and FastAPI
- Kubernetes/Helm Charts skill: K8s manifest and Helm chart templates

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developer can deploy the full stack to Minikube with a single command and have all services running within 2 minutes.
- **SC-002**: Developer can access the Todo Chatbot UI through their browser and complete a full user journey (create, view, update, delete a todo) using the locally deployed stack.
- **SC-003**: Developer can upgrade the deployment with new settings and see changes reflected within 60 seconds.
- **SC-004**: Developer can roll back a failed upgrade to the previous working version within 30 seconds.
- **SC-005**: All three services recover automatically from a pod restart within 60 seconds without manual intervention.
- **SC-006**: Developer can go from a fresh Minikube cluster to a running application in under 10 minutes (including image builds).

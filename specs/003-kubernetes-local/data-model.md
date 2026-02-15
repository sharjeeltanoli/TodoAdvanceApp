# Data Model: Local Kubernetes Deployment

**Feature**: 003-kubernetes-local | **Date**: 2026-02-15

## Kubernetes Resource Model

This feature creates no database entities. The "data model" for this feature is the set of Kubernetes resources managed by the Helm chart.

### Resource Inventory

| Resource | Name Pattern | Count | Purpose |
|----------|-------------|-------|---------|
| Namespace | `todo-app` | 1 | Isolation for all resources |
| Deployment | `todo-app-frontend` | 1 | Frontend pod management |
| Deployment | `todo-app-backend` | 1 | Backend pod management |
| Deployment | `todo-app-mcp` | 1 | MCP server pod management |
| Service | `todo-app-frontend` | 1 | NodePort (30080→3000) |
| Service | `todo-app-backend` | 1 | ClusterIP (8000→8000) |
| Service | `todo-app-mcp` | 1 | ClusterIP (8001→8001) |
| ConfigMap | `todo-app-config` | 1 | Non-sensitive configuration |
| Secret | `todo-app-secret` | 1 | Sensitive credentials |
| Ingress | `todo-app-ingress` | 0-1 | Optional hostname routing |

### Resource Relationships

```
Namespace (todo-app)
├── ConfigMap (todo-app-config)
│   └── Referenced by: all 3 Deployments (envFrom)
├── Secret (todo-app-secret)
│   └── Referenced by: all 3 Deployments (envFrom)
├── Deployment (todo-app-frontend)
│   ├── Uses: ConfigMap, Secret
│   └── Exposed by: Service (NodePort)
├── Deployment (todo-app-backend)
│   ├── Uses: ConfigMap, Secret
│   ├── Connects to: Service (todo-app-mcp)
│   └── Exposed by: Service (ClusterIP)
├── Deployment (todo-app-mcp)
│   ├── Uses: ConfigMap, Secret
│   └── Exposed by: Service (ClusterIP)
└── Ingress (todo-app-ingress) [optional]
    └── Routes to: Service (todo-app-frontend)
```

### Docker Image Artifacts

| Image | Tag Strategy | Build Context | Dockerfile |
|-------|-------------|---------------|------------|
| `todo-frontend` | `latest` (local dev) | `./frontend` | `Dockerfile.frontend` |
| `todo-backend` | `latest` (local dev) | `./backend` | `Dockerfile.backend` |
| `todo-mcp` | `latest` (local dev) | `./backend` | `Dockerfile.mcp` |

### Environment Variable Flow

```
values.yaml
  ├── config.*  →  ConfigMap  →  envFrom  →  Pod env vars
  └── secrets.* →  Secret     →  envFrom  →  Pod env vars
```

### Labels (standard Helm/K8s)

All resources carry these labels:
- `app.kubernetes.io/name`: `todo-app`
- `app.kubernetes.io/instance`: `{{ .Release.Name }}`
- `app.kubernetes.io/component`: `frontend` | `backend` | `mcp`
- `app.kubernetes.io/managed-by`: `Helm`
- `helm.sh/chart`: `todo-app-0.1.0`

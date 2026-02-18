# Dapr Configuration Skill

## When to Use This Skill

Trigger this skill when the user:
- Asks about Dapr component configuration (Pub/Sub, state stores, bindings, secrets)
- Needs to add event-driven messaging between services
- Wants to set up scheduled tasks (cron bindings)
- Needs service-to-service invocation via Dapr
- Is deploying to Kubernetes with Dapr sidecars
- Asks about local development with Dapr
- Needs secret management through Dapr
- References "Phase 5B" (Kafka), "Phase 5C" (cloud), or Dapr-related tasks

## Dapr Building Blocks Overview

| Building Block | Purpose | Local Component | Production Component |
|---|---|---|---|
| **Pub/Sub** | Async messaging between services | Redis Streams | Apache Kafka |
| **State Management** | Key-value state persistence | Redis | PostgreSQL / CosmosDB |
| **Service Invocation** | Service-to-service calls with mTLS | Built-in (sidecar mesh) | Built-in (sidecar mesh) |
| **Bindings** | Trigger/output to external systems | Cron, HTTP | Cron, HTTP, SQS, etc. |
| **Secrets** | Centralized secret access | Local file / env | K8s Secrets / Vault |
| **Observability** | Distributed tracing | Zipkin | Jaeger / App Insights |

## Component Configuration Patterns

### Directory Layout
```
dapr/
├── components/           # Shared components
│   ├── pubsub.yaml
│   ├── statestore.yaml
│   ├── secrets.yaml
│   └── bindings/
│       ├── cron-overdue-check.yaml
│       └── http-notify.yaml
├── subscriptions/        # Pub/Sub subscriptions
│   └── task-events-sub.yaml
└── config.yaml           # Dapr configuration (tracing, mTLS)
```

### Component Scoping
Restrict components to specific app-ids for security:
```yaml
spec:
  metadata:
    - name: allowedTopics
      value: "task-events,reminders,task-updates"
scopes:
  - backend-api
  - mcp-server
```

## Pub/Sub Patterns

### Publishing Events (Python / FastAPI)
```python
import httpx

DAPR_HTTP_PORT = 3500
PUBSUB_NAME = "pubsub"

async def publish_event(topic: str, data: dict):
    """Publish an event to a Dapr Pub/Sub topic."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/{PUBSUB_NAME}/{topic}",
            json=data,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
```

### Subscribing to Events (Python / FastAPI)
```python
from fastapi import FastAPI, Request

app = FastAPI()

# Programmatic subscription: Dapr calls GET /dapr/subscribe
@app.get("/dapr/subscribe")
async def subscribe():
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task",
        },
        {
            "pubsubname": "pubsub",
            "topic": "reminders",
            "route": "/events/reminder",
        },
    ]

@app.post("/events/task")
async def handle_task_event(request: Request):
    event = await request.json()
    data = event.get("data", {})
    # Process event...
    return {"status": "SUCCESS"}
```

### Declarative Subscriptions (YAML)
Use `subscription.yaml.template` for declarative subscriptions that live alongside components.

## State Management

### Get / Set / Delete State (Python)
```python
DAPR_HTTP_PORT = 3500
STATE_STORE = "statestore"

async def save_state(key: str, value: dict):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"http://localhost:{DAPR_HTTP_PORT}/v1.0/state/{STATE_STORE}",
            json=[{"key": key, "value": value}],
        )

async def get_state(key: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"http://localhost:{DAPR_HTTP_PORT}/v1.0/state/{STATE_STORE}/{key}"
        )
        return resp.json() if resp.status_code == 200 else None

async def delete_state(key: str):
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"http://localhost:{DAPR_HTTP_PORT}/v1.0/state/{STATE_STORE}/{key}"
        )
```

### Concurrency Control
Use ETags for optimistic concurrency:
```python
# First read returns an ETag header
resp = await client.get(f"http://localhost:{DAPR_HTTP_PORT}/v1.0/state/{STATE_STORE}/{key}")
etag = resp.headers.get("ETag")

# Write with ETag for first-write-wins
await client.post(
    f"http://localhost:{DAPR_HTTP_PORT}/v1.0/state/{STATE_STORE}",
    json=[{"key": key, "value": new_value, "etag": etag, "options": {"concurrency": "first-write"}}],
)
```

## Service Invocation

### Call Another Service via Dapr
```python
async def invoke_service(app_id: str, method: str, data: dict = None):
    """Invoke a method on another Dapr service."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"http://localhost:{DAPR_HTTP_PORT}/v1.0/invoke/{app_id}/method/{method}",
            json=data,
        )
        resp.raise_for_status()
        return resp.json()

# Example: backend calls MCP server
result = await invoke_service("mcp-server", "tools/list")
```

Benefits over direct HTTP:
- Automatic mTLS encryption
- Built-in retries with backoff
- Service discovery (no hardcoded URLs)
- Distributed tracing propagation

## Cron Bindings for Scheduled Tasks

### How It Works
Dapr calls your app at the configured schedule:
```python
@app.post("/cron/check-overdue")
async def check_overdue_tasks(request: Request):
    """Called by Dapr cron binding every 5 minutes."""
    overdue = await find_overdue_tasks()
    for task in overdue:
        await publish_event("reminders", {
            "type": "overdue",
            "task_id": str(task.id),
            "title": task.title,
            "due_date": task.due_date.isoformat(),
        })
    return {"status": "SUCCESS"}
```

### Schedule Expressions
| Expression | Meaning |
|---|---|
| `@every 5m` | Every 5 minutes |
| `@every 1h` | Every hour |
| `0 */5 * * * *` | Every 5 minutes (cron) |
| `0 0 9 * * *` | Daily at 9 AM |
| `@daily` | Once per day (midnight) |

## Secrets Management

### Access Secrets from Dapr
```python
async def get_secret(secret_name: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"http://localhost:{DAPR_HTTP_PORT}/v1.0/secrets/kubernetes/{secret_name}"
        )
        return resp.json().get(secret_name, "")
```

### Reference Secrets in Components
```yaml
spec:
  metadata:
    - name: connectionString
      secretKeyRef:
        name: db-credentials
        key: connection-string
auth:
  secretStore: kubernetes
```

## Sidecar Injection in Kubernetes

### Required Annotations
```yaml
metadata:
  annotations:
    dapr.io/enabled: "true"
    dapr.io/app-id: "backend-api"
    dapr.io/app-port: "8000"
    dapr.io/app-protocol: "http"
    dapr.io/log-level: "info"
    dapr.io/config: "dapr-config"
    dapr.io/enable-metrics: "true"
    dapr.io/metrics-port: "9090"
```

### Optional Performance Annotations
```yaml
    dapr.io/sidecar-cpu-request: "100m"
    dapr.io/sidecar-memory-request: "128Mi"
    dapr.io/sidecar-cpu-limit: "300m"
    dapr.io/sidecar-memory-limit: "256Mi"
```

## Local Development vs Production

### Local Dev (Minikube / Docker Compose)
```bash
# Install Dapr CLI
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash

# Initialize Dapr (installs Redis, Zipkin in Docker/K8s)
dapr init                     # Docker mode
dapr init -k                  # Kubernetes mode (Minikube)

# Run app with Dapr sidecar
dapr run --app-id backend-api \
         --app-port 8000 \
         --dapr-http-port 3500 \
         --resources-path ./dapr/components \
         -- python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Production (Kubernetes)
```bash
# Install Dapr on cluster
helm repo add dapr https://dapr.github.io/helm-charts/
helm repo update
helm install dapr dapr/dapr --namespace dapr-system --create-namespace --wait

# Apply components
kubectl apply -f dapr/components/
kubectl apply -f dapr/subscriptions/
```

## Dapr CLI Commands Reference

| Command | Description |
|---|---|
| `dapr init` | Install Dapr locally (Docker) |
| `dapr init -k` | Install Dapr in Kubernetes |
| `dapr run --app-id <id> -- <cmd>` | Run app with sidecar |
| `dapr list` | List running Dapr apps |
| `dapr stop --app-id <id>` | Stop a Dapr app |
| `dapr dashboard` | Open Dapr dashboard (port 8080) |
| `dapr publish --pubsub pubsub --topic <t> --data '{}'` | Publish test event |
| `dapr invoke --app-id <id> --method <m>` | Invoke a service method |
| `dapr components -k` | List components in K8s |
| `dapr status -k` | Check Dapr system health in K8s |
| `dapr upgrade -k --runtime-version 1.14` | Upgrade Dapr in K8s |

## Todo App Specific Use Cases

### Topics & Events
| Topic | Publisher | Subscriber | Event Types |
|---|---|---|---|
| `task-events` | backend-api | mcp-server, frontend-sse | created, updated, deleted, completed |
| `reminders` | backend-api (cron) | notification-service | overdue, due-soon, recurring-due |
| `task-updates` | backend-api | frontend (via SSE) | real-time sync for all clients |

### Cron Jobs
| Binding | Schedule | Action |
|---|---|---|
| `cron-overdue-check` | Every 5 min | Find overdue tasks, publish to `reminders` |
| `cron-recurring-tasks` | Every hour | Generate next occurrence of recurring tasks |

### State Store
- Cache conversation history: `conversation:{id}` -> last N messages
- Cache user preferences: `user-prefs:{id}` -> theme, filters, sort
- Rate limiting: `rate:{user_id}:{endpoint}` -> request count with TTL

### Secrets
| Secret Name | Contains |
|---|---|
| `openai-credentials` | `OPENAI_API_KEY` |
| `db-credentials` | `DATABASE_URL`, `DIRECT_URL` |
| `auth-secrets` | `BETTER_AUTH_SECRET` |

## Retry Policies & Circuit Breakers

### Resiliency Configuration
```yaml
apiVersion: dapr.io/v1alpha1
kind: Resiliency
metadata:
  name: todo-app-resiliency
spec:
  policies:
    retries:
      pubsubRetry:
        policy: exponential
        maxInterval: 30s
        maxRetries: 5
      serviceRetry:
        policy: constant
        duration: 3s
        maxRetries: 3
    circuitBreakers:
      simpleCB:
        maxRequests: 1
        interval: 10s
        timeout: 30s
        trip: consecutiveFailures >= 3
  targets:
    apps:
      mcp-server:
        retry: serviceRetry
        circuitBreaker: simpleCB
    components:
      pubsub:
        outbound:
          retry: pubsubRetry
```

## Troubleshooting

### Common Issues
| Issue | Cause | Fix |
|---|---|---|
| Sidecar not injecting | Missing annotation or Dapr not installed | Verify `dapr.io/enabled: "true"` and `dapr status -k` |
| Pub/Sub not delivering | Wrong topic or subscription mismatch | Check `dapr/subscribe` endpoint returns correct routes |
| State store timeout | Connection string wrong | Verify secret reference and test with `dapr invoke` |
| Cron not firing | Wrong schedule format | Use `@every 5m` for simple intervals |
| 500 from sidecar | App not ready when sidecar starts | Add readiness probe, increase `dapr.io/sidecar-listen-addresses` |
| mTLS errors | Certificate expired | Run `dapr mtls renew-certificate -k` |

### Debug Commands
```bash
# Check sidecar logs
kubectl logs <pod> -c daprd

# Test Pub/Sub from CLI
dapr publish --publish-app-id backend-api --pubsub pubsub --topic task-events --data '{"type":"test"}'

# Check component status
kubectl get components.dapr.io -A

# Check subscriptions
kubectl get subscriptions.dapr.io -A

# Verify sidecar is running
curl http://localhost:3500/v1.0/healthz
```

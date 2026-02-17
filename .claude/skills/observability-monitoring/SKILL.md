# Observability and Monitoring Skill

## When to Use This Skill

**Triggers:**
- User asks about logging, metrics, tracing, or alerting
- User mentions Prometheus, Grafana, Loki, Jaeger, or OpenTelemetry
- User wants to monitor application health or performance
- User says "add observability", "set up monitoring", "create dashboards"
- User asks about structured logging for Python/FastAPI or Next.js
- Phase 5C cloud deployment observability setup
- User wants alerting for pod crashes, high latency, or error rates

## The Three Pillars of Observability

```
┌─────────────────────────────────────────────────────────┐
│                    OBSERVABILITY                        │
├──────────────────┬──────────────────┬───────────────────┤
│      LOGS        │     METRICS      │     TRACES        │
│  (What happened) │  (How much/many) │  (Request flow)   │
├──────────────────┼──────────────────┼───────────────────┤
│  Loki + Promtail │  Prometheus      │  Jaeger / Tempo   │
│  structlog/pino  │  Grafana         │  OpenTelemetry    │
│  JSON format     │  RED/USE method  │  Correlation IDs  │
└──────────────────┴──────────────────┴───────────────────┘
```

### Logs — What Happened
- Structured JSON logs (machine-parseable)
- Contextual fields: request_id, user_id, operation, duration
- Levels: DEBUG → INFO → WARN → ERROR → CRITICAL
- Aggregated via Loki (Grafana-native, low cost)

### Metrics — How Much / How Many
- **RED Method** (request-scoped): Rate, Errors, Duration
- **USE Method** (resource-scoped): Utilization, Saturation, Errors
- Collected by Prometheus, visualized in Grafana
- Custom app metrics via `/metrics` endpoint

### Traces — Request Flow
- Distributed tracing across services
- Frontend → Backend → MCP Server → Database
- Correlation IDs link logs + metrics + traces
- Jaeger UI for trace visualization

## Stack Overview

| Component | Purpose | Cost | Alternative |
|-----------|---------|------|-------------|
| **Prometheus** | Metrics collection & storage | Free (in-cluster) | Datadog, New Relic |
| **Grafana** | Dashboards & visualization | Free (in-cluster) | Datadog, Kibana |
| **Loki** | Log aggregation | Free (in-cluster) | ELK Stack, CloudWatch |
| **Promtail** | Log shipping to Loki | Free (in-cluster) | Fluentd, Fluent Bit |
| **Jaeger** | Distributed tracing | Free (in-cluster) | Zipkin, Tempo |
| **AlertManager** | Alert routing & notifications | Free (in-cluster) | PagerDuty, OpsGenie |

**Total cost for in-cluster setup: $0** (runs on existing K8s nodes)

## Quick Start — Install the Full Stack

```bash
# 1. Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update

# 2. Install kube-prometheus-stack (Prometheus + Grafana + AlertManager)
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword="admin" \
  --set prometheus.prometheusSpec.retention=7d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi

# 3. Install Loki + Promtail (log aggregation)
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=10Gi

# 4. Install Jaeger (distributed tracing)
helm install jaeger jaegertracing/jaeger \
  --namespace monitoring \
  --set provisionDataStore.cassandra=false \
  --set allInOne.enabled=true \
  --set storage.type=memory \
  --set agent.enabled=false

# 5. Verify
kubectl get pods -n monitoring
```

## Prometheus Metrics Collection

### How It Works
1. Application exposes metrics at `/metrics` endpoint
2. Prometheus scrapes endpoints on a schedule (default 15s)
3. Metrics stored in time-series database
4. Grafana queries Prometheus for visualization

### Python/FastAPI Metrics
```python
# pip install prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

This auto-instruments:
- `http_requests_total` — request count by method, status, path
- `http_request_duration_seconds` — response time histogram
- `http_requests_in_progress` — concurrent requests gauge

### Custom Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

tasks_created = Counter("tasks_created_total", "Total tasks created", ["user_id"])
task_duration = Histogram("task_operation_seconds", "Task operation duration", ["operation"])
active_users = Gauge("active_users", "Currently active users")
```

### ServiceMonitor (K8s)
Tells Prometheus which services to scrape. See `templates/prometheus-servicemonitor.yaml.template`.

## Grafana Dashboards

### Key Panels for hackathon-todo
1. **Request Rate** — requests/sec by endpoint
2. **Error Rate** — 4xx and 5xx responses/sec
3. **Response Time** — p50, p95, p99 latency
4. **Active Users** — gauge of concurrent users
5. **Tasks Created/Hour** — task creation throughput
6. **Pod CPU/Memory** — resource utilization
7. **DB Connection Pool** — active/idle connections
8. **Pod Restart Count** — stability indicator

### Access Grafana
```bash
# Port-forward to localhost
kubectl port-forward svc/monitoring-grafana 3001:80 -n monitoring

# Open http://localhost:3001
# Login: admin / admin (change in production!)
```

### Add Loki as Data Source
1. Grafana → Configuration → Data Sources → Add
2. Select "Loki"
3. URL: `http://loki:3100`
4. Save & Test

## Loki Log Aggregation

### How It Works
```
App → stdout/stderr → Container runtime → Promtail → Loki → Grafana
```

1. Apps log to stdout in JSON format
2. Promtail collects logs from all pods
3. Loki indexes and stores logs
4. Grafana queries Loki via LogQL

### LogQL Examples
```logql
# All backend logs
{namespace="production", app="backend"}

# Error logs only
{namespace="production", app="backend"} |= "ERROR"

# JSON-parsed query
{namespace="production", app="backend"} | json | level="error" | status >= 500

# Count errors per minute
rate({namespace="production", app="backend"} |= "ERROR" [1m])

# Top 5 slowest endpoints
topk(5, avg by(path) (
  {namespace="production", app="backend"} | json | unwrap duration_ms [5m]
))
```

## Jaeger Distributed Tracing

### How It Works
```
Frontend → Backend → MCP Server → Database
   │          │          │           │
   └──────────┴──────────┴───────────┘
              Jaeger Trace
```

Each request gets a trace ID that propagates across services via HTTP headers (`traceparent`).

### Python/FastAPI Integration
```python
# pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup
provider = TracerProvider()
exporter = JaegerExporter(agent_host_name="jaeger-agent", agent_port=6831)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
```

### Access Jaeger UI
```bash
kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring
# Open http://localhost:16686
```

## Alert Rules and Notifications

### Alert Categories

| Category | Metric | Threshold | Severity |
|----------|--------|-----------|----------|
| **Availability** | Pod restart count | > 3 in 15m | critical |
| **Availability** | Pod not ready | > 5m | critical |
| **Performance** | p95 latency | > 2s | warning |
| **Performance** | p99 latency | > 5s | critical |
| **Errors** | 5xx error rate | > 5% | warning |
| **Errors** | 5xx error rate | > 15% | critical |
| **Resources** | CPU utilization | > 85% | warning |
| **Resources** | Memory utilization | > 90% | critical |
| **Database** | Connection errors | > 0 in 5m | critical |
| **Custom** | Task creation failures | > 10 in 5m | warning |

### Notification Channels
```yaml
# AlertManager config for Slack
route:
  receiver: slack-notifications
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
receivers:
  - name: slack-notifications
    slack_configs:
      - api_url: "https://hooks.slack.com/services/XXX"
        channel: "#alerts"
        title: "{{ .GroupLabels.alertname }}"
        text: "{{ .CommonAnnotations.summary }}"
```

## Python Structured Logging (FastAPI)

### Setup with structlog
```bash
pip install structlog python-json-logger
```

### Key Principles
- **JSON format** — machine parseable, Loki-friendly
- **Correlation IDs** — link logs across a request lifecycle
- **Contextual fields** — user_id, operation, duration_ms
- **No PII in logs** — never log passwords, tokens, emails

### What to Log
```
INFO  — task.created    {task_id, user_id, title}
INFO  — task.updated    {task_id, user_id, changes}
INFO  — task.deleted    {task_id, user_id}
INFO  — auth.login      {user_id, method}
WARN  — auth.failed     {ip, method, reason}
ERROR — db.connection   {error, retry_count}
ERROR — api.error       {path, method, status, error}
```

See `templates/structured-logging-python.template` for full implementation.

## Next.js Logging Patterns

### Setup with pino
```bash
npm install pino pino-pretty
```

### Key Principles
- Use `pino` for structured JSON logging
- Log in API routes and server components
- Client-side: minimal logging (errors only)
- Include request context (path, method, user)

See `templates/structured-logging-nextjs.template` for full implementation.

## Kubernetes Health Monitoring

### Built-in Metrics (via kube-state-metrics)
```promql
# Pod restart rate
rate(kube_pod_container_status_restarts_total{namespace="production"}[15m])

# Pods not ready
kube_pod_status_ready{namespace="production", condition="false"}

# Node CPU usage
100 - (avg by(node) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Node memory usage
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# PVC usage
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 100
```

### Health Check Endpoints
```python
# Backend /api/health
@app.get("/api/health")
async def health():
    # Check DB connection
    try:
        await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Dapr Observability Integration

If using Dapr sidecar, observability comes built-in:

```yaml
# Dapr configuration for observability
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: appconfig
spec:
  tracing:
    samplingRate: "1"    # 100% sampling (reduce in production)
    zipkin:
      endpointAddress: "http://jaeger-collector.monitoring:9411/api/v2/spans"
  metric:
    enabled: true
    rules:
      - name: dapr_http_server_request_count
        labels:
          - name: method
          - name: path
  logging:
    apiLogging:
      enabled: true
      obfuscateURLs: false
```

Dapr automatically provides:
- Distributed tracing (propagates trace context)
- Metrics (request count, latency, errors per sidecar)
- Structured logging (JSON format)

## Cost-Effective Setup for Small Teams

### Tier 1: Free (kubectl only) — $0/mo
```bash
kubectl logs -f deployment/backend -n production
kubectl top pods -n production
kubectl get events -n production --sort-by=.lastTimestamp
```

### Tier 2: In-Cluster Stack — $0/mo (uses existing nodes)
- kube-prometheus-stack (Prometheus + Grafana + AlertManager)
- Loki + Promtail for logs
- 7-day retention, 10GB storage
- Adds ~500MB RAM, ~200m CPU overhead

### Tier 3: Managed Services — $20-100/mo
- Grafana Cloud Free Tier (10k metrics, 50GB logs, 50GB traces)
- DigitalOcean Monitoring (free with cluster)
- Better for production: no maintenance, longer retention

### Optimization Tips
- Scrape interval: 30s (not 15s) for non-critical metrics
- Drop high-cardinality labels (user_id, request_id in metrics)
- Use recording rules for frequently-queried expressions
- Set retention: 7 days dev, 30 days production
- Sample traces at 10-20% in production (not 100%)

## Retention Policies

| Environment | Metrics | Logs | Traces |
|-------------|---------|------|--------|
| Development | 3 days | 3 days | 1 day |
| Staging | 7 days | 7 days | 3 days |
| Production | 30 days | 30 days | 7 days |

## Template Files

| Template | Purpose |
|----------|---------|
| `prometheus-servicemonitor.yaml.template` | Prometheus scraping config for app services |
| `grafana-dashboard.json.template` | Pre-built dashboard with key panels |
| `loki-config.yaml.template` | Loki log aggregation configuration |
| `jaeger-deployment.yaml.template` | Jaeger all-in-one tracing deployment |
| `alertmanager-rules.yaml.template` | Alert rules for availability, perf, errors |
| `structured-logging-python.template` | Python/FastAPI structured logging setup |
| `structured-logging-nextjs.template` | Next.js/pino structured logging setup |

## Example Files

| Example | Purpose |
|---------|---------|
| `todo-app-prometheus-example.yaml` | Complete Prometheus setup for hackathon-todo |
| `todo-app-grafana-dashboard-example.json` | Ready-to-import Grafana dashboard |
| `python-structured-logging-example.py` | Working FastAPI logging implementation |
| `nextjs-logging-example.ts` | Working Next.js logging implementation |

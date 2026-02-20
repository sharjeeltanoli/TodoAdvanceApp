# Monitoring Runbook

**Stack**: Prometheus + Grafana + AlertManager + Loki + Promtail (all in `monitoring` namespace)

---

## Access Grafana Dashboard

```bash
# Port-forward Grafana to localhost:3001
kubectl port-forward svc/monitoring-grafana 3001:80 -n monitoring

# Open in browser: http://localhost:3001
# Username: admin
# Password: retrieve from secret:
kubectl get secret monitoring-grafana -n monitoring \
  -o jsonpath='{.data.admin-password}' | base64 --decode
```

---

## Key Dashboards

Import these from Grafana.com (Dashboards → + Import → paste ID):

| Dashboard | ID | Purpose |
|-----------|-----|---------|
| Kubernetes / Namespaces | 15758 | Pod count, CPU, memory per namespace |
| Node Exporter Full | 1860 | Node-level CPU, memory, disk, network |
| Kubernetes / Pods | 6781 | Per-pod resource breakdown |

**Custom TODO App RED metrics** (request rate / error rate / duration):
- After deployment, navigate to: Explore → Prometheus
- Query examples:
  ```promql
  # Request rate (backend)
  rate(http_requests_total{namespace="production"}[5m])

  # Error rate (5xx only)
  rate(http_requests_total{status=~"5..",namespace="production"}[5m])
    / rate(http_requests_total{namespace="production"}[5m])

  # P95 latency
  histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{namespace="production"}[5m]))
  ```

---

## Access Logs (Loki via Grafana Explore)

```
Grafana → Explore → Data Source: Loki
```

**Useful LogQL queries**:
```logql
# All backend logs in production
{namespace="production", app="todo-app-backend"}

# Error logs only
{namespace="production"} |= "ERROR"

# Frontend request logs
{namespace="production", app="todo-app-frontend"} | json

# SSE gateway connection events
{namespace="production", app="todo-app-sse-gateway"} |= "connection"
```

---

## Add Loki Data Source

If Loki is not already configured in Grafana:
1. Grafana → Connections → Data Sources → Add → Loki
2. URL: `http://loki:3100`
3. Save & Test

---

## Alerts (AlertManager)

**Active alert rules** (from `chart/templates/monitoring/alerting-rules.yaml`):

| Alert | Condition | Severity |
|-------|-----------|----------|
| `HighErrorRate` | HTTP 5xx > 5% for 5 min | warning |
| `CriticalErrorRate` | HTTP 5xx > 15% for 2 min | critical |
| `PodCrashLooping` | restart rate > 0.2 for 5 min | critical |

**View AlertManager UI**:
```bash
kubectl port-forward svc/monitoring-alertmanager 9093:9093 -n monitoring
# Open: http://localhost:9093
```

**Configure Slack notifications** (optional):
```bash
helm upgrade monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --reuse-values \
  --set "alertmanager.config.receivers[0].name=slack" \
  --set "alertmanager.config.receivers[0].slack_configs[0].api_url=<SLACK_WEBHOOK_URL>" \
  --set "alertmanager.config.receivers[0].slack_configs[0].channel=#alerts-production"
```

---

## Metrics Endpoints

Verify services are exposing metrics:
```bash
# Port-forward backend and check /metrics
kubectl port-forward deployment/todo-app-backend 8000:8000 -n production
curl http://localhost:8000/metrics | head -20
```

---

## Verify ServiceMonitors

```bash
# List ServiceMonitors in production namespace
kubectl get servicemonitor -n production

# Verify Prometheus has discovered the targets
kubectl port-forward svc/monitoring-kube-prometheus-sta-prometheus 9090:9090 -n monitoring
# Open: http://localhost:9090/targets
# → Look for todo-app-backend and todo-app-notification targets as "UP"
```

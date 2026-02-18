# Quickstart: Event-Driven Todo System

**Feature**: 005-event-driven | **Prereqs**: Minikube running, kubectl, Helm 3

## 1. Install Dapr

```bash
# Install Dapr CLI
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash

# Install Dapr on Minikube
dapr init -k --wait

# Verify
dapr status -k
```

## 2. Install Redpanda (Kafka-compatible broker)

```bash
helm repo add redpanda https://charts.redpanda.com
helm repo update

helm install redpanda redpanda/redpanda \
  --set statefulset.replicas=1 \
  --set resources.cpu.cores=1 \
  --set resources.memory.container.max=256Mi \
  --set storage.persistentVolume.size=2Gi \
  --set console.enabled=true

# Wait for ready
kubectl rollout status statefulset/redpanda --timeout=300s
```

## 3. Install Redis (Dapr state store)

```bash
helm install redis oci://registry-1.docker.io/bitnamicharts/redis \
  --set architecture=standalone \
  --set auth.enabled=false \
  --set master.persistence.size=1Gi
```

## 4. Apply Dapr Components

```bash
kubectl apply -f dapr/components/
kubectl apply -f dapr/subscriptions/
kubectl apply -f dapr/config.yaml
kubectl apply -f dapr/resiliency.yaml

# Verify
kubectl get components.dapr.io
kubectl get subscriptions.dapr.io
```

## 5. Run Database Migration

```bash
# From backend directory
cd backend
alembic upgrade head
```

## 6. Deploy Application

```bash
# Build images (from repo root)
eval $(minikube docker-env)
docker build -f Dockerfile.backend -t todo-backend:latest .
docker build -f Dockerfile.frontend -t todo-frontend:latest .
docker build -f backend/services/notification/Dockerfile -t todo-notification:latest .
docker build -f backend/services/sse_gateway/Dockerfile -t todo-sse-gateway:latest .

# Deploy with Helm
helm upgrade --install todo-app ./chart -f chart/values.yaml
```

## 7. Verify Event Flow

```bash
# Check all pods have Dapr sidecars
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{","}{end}{"\n"}{end}'

# Test publish an event
dapr publish --publish-app-id backend-api --pubsub pubsub --topic task-events --data '{"event_type":"test","task_id":"123"}'

# Check Redpanda Console
kubectl port-forward svc/redpanda-console 8080:8080
# Open http://localhost:8080

# Check Dapr dashboard
dapr dashboard -k
# Opens http://localhost:8080 (or next free port)
```

## 8. Test Real-Time Sync

```bash
# Open SSE stream (in one terminal)
curl -N -H "Authorization: Bearer <your-token>" http://localhost:30080/api/stream/tasks

# Create a task (in another terminal)
curl -X POST http://localhost:30080/api/todos \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test event-driven", "priority": "high"}'

# The SSE stream should receive a task-changed event within 2 seconds
```

## Useful Commands

```bash
# Dapr status
dapr status -k
dapr components -k
dapr dashboard -k

# Redpanda topics
kubectl exec -it redpanda-0 -- rpk topic list
kubectl exec -it redpanda-0 -- rpk topic consume task-events --num 5

# Logs
kubectl logs -l app=backend -c daprd     # Dapr sidecar logs
kubectl logs -l app=backend -c backend   # App logs
kubectl logs -l app=notification-svc     # Notification service
kubectl logs -l app=sse-gateway          # SSE gateway
```

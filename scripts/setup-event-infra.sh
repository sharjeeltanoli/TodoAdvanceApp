#!/usr/bin/env bash
# Phase 1: Event-Driven Infrastructure Setup for Minikube
# Installs Dapr, Redpanda, Redis and creates Kafka topics
set -euo pipefail

echo "=== Phase 1: Event-Driven Infrastructure Setup ==="

# T001: Install Dapr on Minikube
echo ""
echo "--- T001: Installing Dapr on Minikube ---"
if ! command -v dapr &>/dev/null; then
  echo "Installing Dapr CLI..."
  curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash
fi
echo "Installing Dapr on Kubernetes cluster..."
dapr init -k --wait --timeout 300
echo "Verifying Dapr installation..."
dapr status -k
echo "T001 DONE: Dapr installed and verified"

# T002: Install Redpanda via Helm
echo ""
echo "--- T002: Installing Redpanda (Kafka-compatible broker) ---"
helm repo add redpanda https://charts.redpanda.com 2>/dev/null || true
helm repo update
helm install redpanda redpanda/redpanda \
  --set statefulset.replicas=1 \
  --set resources.cpu.cores=1 \
  --set resources.memory.container.max=256Mi \
  --set storage.persistentVolume.size=2Gi \
  --set console.enabled=true \
  --wait --timeout 5m
echo "Waiting for Redpanda to be ready..."
kubectl rollout status statefulset/redpanda --timeout=300s
echo "T002 DONE: Redpanda installed and ready"

# T003: Install Redis via Helm (can run in parallel with T002)
echo ""
echo "--- T003: Installing Redis (Dapr state store) ---"
helm install redis oci://registry-1.docker.io/bitnamicharts/redis \
  --set architecture=standalone \
  --set auth.enabled=false \
  --set master.persistence.size=1Gi \
  --wait --timeout 5m
echo "T003 DONE: Redis installed"

# T004: Create Kafka topics on Redpanda
echo ""
echo "--- T004: Creating Kafka topics ---"
echo "Waiting for Redpanda broker to accept connections..."
kubectl wait --for=condition=Ready pod/redpanda-0 --timeout=120s

# Create topics with partition counts per plan
kubectl exec -it redpanda-0 -- rpk topic create task-events --partitions 3 --replicas 1 || true
kubectl exec -it redpanda-0 -- rpk topic create reminders --partitions 1 --replicas 1 || true
kubectl exec -it redpanda-0 -- rpk topic create task-updates --partitions 3 --replicas 1 || true

echo "Verifying topics..."
kubectl exec -it redpanda-0 -- rpk topic list

echo ""
echo "T004 DONE: Topics created"

echo ""
echo "=== Phase 1 Complete ==="
echo "Infrastructure ready: Dapr, Redpanda, Redis running on Minikube"
echo ""
echo "Next steps:"
echo "  1. Apply Dapr components: kubectl apply -f dapr/"
echo "  2. Run database migration: cd backend && alembic upgrade head"
echo "  3. Deploy app: helm upgrade --install todo-app ./chart -f chart/values.yaml"

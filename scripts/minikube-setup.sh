#!/usr/bin/env bash
set -euo pipefail

# Todo Chatbot — Minikube Full Stack Setup
# Usage: ./scripts/minikube-setup.sh
#
# Required environment variables:
#   DATABASE_URL          — Neon PostgreSQL connection string
#   BETTER_AUTH_SECRET    — Auth secret key
#   OPENAI_API_KEY        — OpenAI API key
#   FRONTEND_DATABASE_URL — Frontend DB connection string (Better Auth)
#
# Optional:
#   OPENAI_BASE_URL       — Custom OpenAI-compatible endpoint

NAMESPACE="todo-app"
RELEASE_NAME="todo-app"

# ─── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ─── Step 1: Check Prerequisites ────────────────────────────────────
info "Checking prerequisites..."

for cmd in docker minikube helm kubectl; do
  if ! command -v "$cmd" &>/dev/null; then
    error "'$cmd' is not installed. Please install it first."
  fi
done

info "All prerequisites found."

# ─── Step 2: Check Required Env Vars ────────────────────────────────
info "Checking required environment variables..."

missing=()
for var in DATABASE_URL BETTER_AUTH_SECRET OPENAI_API_KEY FRONTEND_DATABASE_URL; do
  if [[ -z "${!var:-}" ]]; then
    missing+=("$var")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  error "Missing required environment variables: ${missing[*]}\n  Export them before running this script."
fi

info "All required environment variables set."

# ─── Step 3: Start Minikube ─────────────────────────────────────────
if minikube status --format='{{.Host}}' 2>/dev/null | grep -q Running; then
  info "Minikube is already running."
else
  info "Starting Minikube..."
  minikube start --cpus=4 --memory=8192 --driver=docker
fi

# ─── Step 4: Configure Docker to Use Minikube ───────────────────────
info "Pointing Docker to Minikube daemon..."
eval "$(minikube docker-env)"

# ─── Step 5: Build Docker Images ────────────────────────────────────
info "Building Docker images (this may take a few minutes)..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

info "  Building frontend..."
docker build -f "$REPO_ROOT/Dockerfile.frontend" -t todo-frontend:latest "$REPO_ROOT/frontend"

info "  Building backend..."
docker build -f "$REPO_ROOT/Dockerfile.backend" -t todo-backend:latest "$REPO_ROOT/backend"

info "  Building MCP server..."
docker build -f "$REPO_ROOT/Dockerfile.mcp" -t todo-mcp:latest "$REPO_ROOT/backend"

info "All images built successfully."

# ─── Step 6: Deploy with Helm ───────────────────────────────────────
info "Deploying with Helm..."

# Check if already installed
if helm status "$RELEASE_NAME" -n "$NAMESPACE" &>/dev/null; then
  info "Existing release found — upgrading..."
  helm upgrade "$RELEASE_NAME" "$REPO_ROOT/chart" \
    --namespace "$NAMESPACE" \
    --set secrets.databaseUrl="$DATABASE_URL" \
    --set secrets.betterAuthSecret="$BETTER_AUTH_SECRET" \
    --set secrets.openaiApiKey="$OPENAI_API_KEY" \
    --set secrets.frontendDatabaseUrl="$FRONTEND_DATABASE_URL" \
    ${OPENAI_BASE_URL:+--set config.openaiBaseUrl="$OPENAI_BASE_URL"}
else
  helm install "$RELEASE_NAME" "$REPO_ROOT/chart" \
    --namespace "$NAMESPACE" \
    --create-namespace \
    --set secrets.databaseUrl="$DATABASE_URL" \
    --set secrets.betterAuthSecret="$BETTER_AUTH_SECRET" \
    --set secrets.openaiApiKey="$OPENAI_API_KEY" \
    --set secrets.frontendDatabaseUrl="$FRONTEND_DATABASE_URL" \
    ${OPENAI_BASE_URL:+--set config.openaiBaseUrl="$OPENAI_BASE_URL"}
fi

# ─── Step 7: Wait for Pods ──────────────────────────────────────────
info "Waiting for pods to be ready (timeout: 120s)..."

kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=todo-app \
  -n "$NAMESPACE" \
  --timeout=120s

# ─── Step 8: Print Status ──────────────────────────────────────────
echo ""
info "Deployment complete!"
echo ""
kubectl get pods -n "$NAMESPACE"
echo ""

FRONTEND_URL=$(minikube service "$RELEASE_NAME-frontend" -n "$NAMESPACE" --url 2>/dev/null || echo "http://localhost:30080")
info "Frontend URL: $FRONTEND_URL"
echo ""
info "Useful commands:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl logs -l app.kubernetes.io/component=frontend -n $NAMESPACE"
echo "  kubectl logs -l app.kubernetes.io/component=backend -n $NAMESPACE"
echo "  helm upgrade $RELEASE_NAME ./chart -n $NAMESPACE --reuse-values"
echo "  helm uninstall $RELEASE_NAME -n $NAMESPACE"

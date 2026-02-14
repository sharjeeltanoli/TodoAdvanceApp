# Kubernetes & Helm Charts Skill

## When to Use This Skill

**Triggers:**
- User needs Kubernetes manifests for deploying containerized apps
- User asks for Helm chart generation
- User wants to deploy to Minikube, DigitalOcean, Azure AKS, or GCP GKE
- User mentions K8s deployment, pods, services, ingress, or scaling
- User needs multi-environment Kubernetes configuration

## Quick Start

### Generate a Basic Deployment
```bash
# From templates, generate a deployment for your app
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Generate a Helm Chart
```bash
helm create my-app        # Scaffold
helm install my-app ./my-app --namespace my-ns --create-namespace
helm upgrade my-app ./my-app --values values-prod.yaml
```

---

## Kubernetes Manifest Generation Patterns

### 1. Deployment Pattern
Use `templates/deployment.yaml.template` for stateless workloads.

**Key decisions:**
- `replicas`: Start with 2 for HA, 1 for dev
- `strategy`: RollingUpdate (default) or Recreate (for stateful single-instance)
- `resources`: Always set requests AND limits
- `probes`: Always configure liveness + readiness; add startup for slow-starting apps

### 2. Service Pattern
Use `templates/service.yaml.template` to expose pods.

| Service Type   | Use Case                          | Environment |
|---------------|-----------------------------------|-------------|
| ClusterIP     | Internal communication            | All         |
| NodePort      | Direct node access                | Dev/Minikube|
| LoadBalancer  | External traffic (cloud)          | Staging/Prod|

### 3. ConfigMap vs Secret

| Data Type           | Use          | Example                    |
|--------------------|--------------|----------------------------|
| App config         | ConfigMap    | LOG_LEVEL, API_URL         |
| Feature flags      | ConfigMap    | ENABLE_FEATURE_X           |
| DB credentials     | Secret       | DATABASE_URL, DB_PASSWORD  |
| API keys           | Secret       | STRIPE_KEY, JWT_SECRET     |
| TLS certificates   | Secret (tls) | server.crt, server.key     |

### 4. Ingress Pattern
Use `templates/ingress.yaml.template` for HTTP routing.

**Supported controllers:**
- nginx (default, works everywhere)
- traefik (lightweight, Minikube default in some setups)
- cloud-native (ALB on AWS, Application Gateway on Azure)

### 5. Storage Pattern
```yaml
# PersistentVolumeClaim for stateful data
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .appName }}-data
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: {{ .storageClass | default "standard" }}
  resources:
    requests:
      storage: {{ .storageSize | default "5Gi" }}
```

---

## Health Check Configuration

### Liveness Probe
Restarts the container if it fails. Use for deadlock detection.
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: http
  initialDelaySeconds: 15
  periodSeconds: 20
  failureThreshold: 3
```

### Readiness Probe
Removes pod from service endpoints if it fails. Use for dependency checks.
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3
```

### Startup Probe
Disables liveness/readiness until app is started. Use for slow-starting apps.
```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: http
  failureThreshold: 30
  periodSeconds: 10
```

---

## Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ .appName }}-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ .appName }}
  minReplicas: {{ .minReplicas | default 2 }}
  maxReplicas: {{ .maxReplicas | default 10 }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## Multi-Environment Configuration

### Directory Structure
```
k8s/
  base/                    # Shared manifests
    deployment.yaml
    service.yaml
    configmap.yaml
  overlays/
    dev/
      kustomization.yaml   # Patches for dev
      configmap-patch.yaml
    staging/
      kustomization.yaml
      configmap-patch.yaml
    prod/
      kustomization.yaml
      configmap-patch.yaml
      hpa.yaml             # Only in prod
```

### Environment Differences

| Setting            | Dev (Minikube)   | Staging          | Production       |
|-------------------|------------------|------------------|------------------|
| Replicas          | 1                | 2                | 3+               |
| CPU request       | 50m              | 100m             | 250m             |
| CPU limit         | 200m             | 500m             | 1000m            |
| Memory request    | 64Mi             | 128Mi            | 256Mi            |
| Memory limit      | 256Mi            | 512Mi            | 1Gi              |
| HPA               | Disabled         | Optional         | Enabled          |
| Ingress TLS       | Self-signed      | Let's Encrypt    | Let's Encrypt    |
| Image pull policy | IfNotPresent     | Always           | Always           |
| Log level         | DEBUG            | INFO             | WARN             |

---

## Helm Chart Best Practices

### Chart Structure
```
my-app/
  Chart.yaml              # Chart metadata
  values.yaml             # Default values
  values-dev.yaml         # Dev overrides
  values-staging.yaml     # Staging overrides
  values-prod.yaml        # Production overrides
  templates/
    _helpers.tpl           # Template helpers
    deployment.yaml
    service.yaml
    configmap.yaml
    secret.yaml
    ingress.yaml
    hpa.yaml
    NOTES.txt              # Post-install instructions
  charts/                  # Subcharts (dependencies)
```

### Values Parameterization
- Use `{{ .Values.* }}` for all configurable fields
- Provide sensible defaults in `values.yaml`
- Use `{{ include "app.fullname" . }}` for consistent naming
- Use `{{ toYaml .Values.resources | nindent 12 }}` for nested YAML

### Helper Templates (_helpers.tpl)
```yaml
{{- define "app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "app.labels" -}}
helm.sh/chart: {{ include "app.chart" . }}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```

---

## Security Best Practices

### Pod Security Context
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000

containerSecurityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ .appName }}-netpol
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: {{ .appName }}
  policyTypes: ["Ingress", "Egress"]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: ingress-nginx
      ports:
        - port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: postgres
      ports:
        - port: 5432
```

---

## Cloud-Specific Notes

### Minikube (Phase 4 - Local Development)
```bash
minikube start --cpus=4 --memory=8192 --driver=docker
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# Use minikube's Docker daemon
eval $(minikube docker-env)

# Access services
minikube service my-app --url
minikube tunnel  # For LoadBalancer services
```

### DigitalOcean Kubernetes (DOKS)
- Use `do-block-storage` storage class
- Load Balancer auto-provisioned via Service type=LoadBalancer
- Use `doctl kubernetes cluster kubeconfig save <cluster>`

### Azure AKS
- Use `managed-premium` or `default` storage class
- Azure Application Gateway for ingress (optional)
- Use `az aks get-credentials --resource-group <rg> --name <cluster>`

### Google GKE
- Use `standard` or `premium-rwo` storage class
- GCE Ingress controller available by default
- Use `gcloud container clusters get-credentials <cluster> --zone <zone>`

---

## Common Commands Reference

```bash
# Apply manifests
kubectl apply -f k8s/ --namespace my-ns

# Helm operations
helm install my-app ./chart --namespace my-ns --create-namespace
helm upgrade my-app ./chart --values values-prod.yaml
helm rollback my-app 1
helm uninstall my-app

# Debugging
kubectl get pods -n my-ns
kubectl describe pod <pod-name> -n my-ns
kubectl logs <pod-name> -n my-ns --follow
kubectl exec -it <pod-name> -n my-ns -- /bin/sh
kubectl port-forward svc/my-app 8080:80 -n my-ns

# Scaling
kubectl scale deployment my-app --replicas=3 -n my-ns
kubectl autoscale deployment my-app --min=2 --max=10 --cpu-percent=70

# Resource usage
kubectl top pods -n my-ns
kubectl top nodes
```

---

## Template Reference

| Template                         | Purpose                              |
|---------------------------------|--------------------------------------|
| `deployment.yaml.template`      | Pod deployment with best practices   |
| `service.yaml.template`         | Service exposure                     |
| `configmap.yaml.template`       | Non-sensitive configuration          |
| `secret.yaml.template`          | Sensitive data                       |
| `ingress.yaml.template`         | HTTP routing and TLS                 |
| `helm-chart-structure.template` | Full Helm chart scaffold             |
| `values.yaml.template`          | Parameterized Helm values            |

## Example Reference

| Example                                | Description                         |
|----------------------------------------|-------------------------------------|
| `frontend-deployment-example.yaml`     | Next.js/React frontend deployment   |
| `backend-deployment-example.yaml`      | FastAPI/Node.js backend deployment  |
| `fullstack-helm-chart-example/`        | Complete Helm chart for full stack  |
| `minikube-setup-example.yaml`          | Local dev cluster configuration     |

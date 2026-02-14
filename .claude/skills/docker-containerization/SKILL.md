# Docker Containerization Skill

## Overview

Generate production-ready Dockerfiles and docker-compose configurations for modern web applications. Supports Next.js, FastAPI, Python, and Node.js stacks with security hardening, multi-stage builds, and orchestration patterns.

## When to Use This Skill

**Triggers:**
- User asks to "dockerize", "containerize", or "add Docker support"
- User needs a Dockerfile, docker-compose, or container configuration
- User wants to deploy an application with containers
- User mentions Docker, containers, or container orchestration
- Project needs production deployment packaging

## Templates

| Template | Path | Use Case |
|----------|------|----------|
| Next.js Dockerfile | `templates/dockerfile-nextjs.template` | Next.js apps with standalone output |
| FastAPI Dockerfile | `templates/dockerfile-fastapi.template` | Python FastAPI services |
| Python Dockerfile | `templates/dockerfile-python.template` | General Python applications |
| docker-compose | `templates/docker-compose.template` | Multi-service orchestration |
| .dockerignore | `templates/dockerignore.template` | Build context exclusions |

## Production Optimization Techniques

### Multi-Stage Builds

All templates use multi-stage builds to minimize final image size:

1. **deps** stage - Install dependencies only (cached layer)
2. **build** stage - Compile/build application
3. **runner** stage - Minimal runtime with only production artifacts

Benefits:
- Final image contains no build tools, source code, or dev dependencies
- Dramatically smaller images (often 10x reduction)
- Reduced attack surface

### Layer Caching Strategy

Order Dockerfile instructions from least to most frequently changing:

```
1. Base image (rarely changes)
2. System packages (infrequent)
3. Dependency lockfiles COPY (changes when deps update)
4. Dependency install (cached if lockfile unchanged)
5. Source code COPY (changes every build)
6. Build command (runs every build)
```

Key rules:
- COPY lockfiles before source code
- Use `.dockerignore` to exclude unnecessary files
- Pin dependency versions for reproducible builds

### Image Size Optimization

- Use `alpine` or `slim` base images
- Remove package manager caches in the same RUN layer
- Use `--no-cache` flags for apk/pip
- Copy only needed artifacts to final stage
- Use `.dockerignore` aggressively

## Security Best Practices

### Non-Root User

All templates create and switch to a non-root user:

```dockerfile
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser
USER appuser
```

### Minimal Base Images

- Node.js: `node:<version>-alpine`
- Python: `python:<version>-slim` (alpine has musl issues with some packages)
- Use specific version tags, never `latest`

### Security Hardening Checklist

- [ ] Non-root user configured
- [ ] No secrets in build args or image layers
- [ ] Minimal base image selected
- [ ] No unnecessary packages installed
- [ ] Read-only filesystem where possible
- [ ] Health checks configured
- [ ] Resource limits set in compose

## Health Checks

Every production container should include a health check:

```dockerfile
# HTTP service
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# TCP service
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD pg_isready -U postgres || exit 1
```

## Environment Variable Handling

### Build-Time Variables (ARG)

Use for values needed during build only:

```dockerfile
ARG NODE_ENV=production
ARG PYTHON_VERSION=3.13
```

### Runtime Variables (ENV)

Use for values needed at runtime:

```dockerfile
ENV NODE_ENV=production
ENV PORT=3000
```

### Secrets

Never put secrets in Dockerfiles. Use:
- `docker-compose.yml` environment section with `.env` file
- Docker secrets for swarm deployments
- Cloud provider secret managers

## Volume Management

### Development Volumes

Bind-mount source code for hot reload:

```yaml
volumes:
  - ./src:/app/src:ro        # Source code (read-only)
  - /app/node_modules         # Exclude node_modules (use container's)
```

### Production Volumes

Named volumes for persistent data:

```yaml
volumes:
  postgres_data:
    driver: local
```

## Network Configuration

### Service Discovery

Docker Compose creates a default network. Services reference each other by service name:

```yaml
services:
  backend:
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/mydb
  db:
    image: postgres:17-alpine
```

### Network Isolation

Separate frontend and backend networks:

```yaml
networks:
  frontend:
  backend:

services:
  web:
    networks: [frontend, backend]
  api:
    networks: [backend]
  db:
    networks: [backend]
```

## Usage

### Generate Dockerfile for Next.js

Read `templates/dockerfile-nextjs.template` and adapt:
- Replace `{{NODE_VERSION}}` with project's Node version
- Replace `{{PACKAGE_MANAGER}}` with npm/pnpm/yarn/bun
- Replace `{{PORT}}` with the application port

### Generate Dockerfile for FastAPI

Read `templates/dockerfile-fastapi.template` and adapt:
- Replace `{{PYTHON_VERSION}}` with project's Python version
- Replace `{{APP_MODULE}}` with the ASGI module path
- Replace `{{PORT}}` with the application port

### Generate Full Stack Compose

Read `templates/docker-compose.template` and adapt:
- Configure services for the project's stack
- Set environment variables from `.env`
- Configure volumes and networks

## Quick Reference

| Concern | Solution |
|---------|----------|
| Small images | Multi-stage + alpine/slim |
| Fast builds | Layer caching + .dockerignore |
| Security | Non-root user + minimal base |
| Reliability | Health checks + restart policies |
| Secrets | .env files + never in Dockerfile |
| Dev experience | Bind mounts + hot reload |
| Data persistence | Named volumes |
| Service communication | Docker networks + service names |

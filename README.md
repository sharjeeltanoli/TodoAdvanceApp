# Todo App — AI-Powered Task Management Platform

> A modern, full-stack todo application that evolves from a simple CRUD web app into a sophisticated, event-driven, cloud-native AI system. Demonstrates spec-driven development, microservices, real-time sync, and natural language task management.

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

This project is a reference implementation of a production-quality task management platform, built incrementally across five feature phases using **Spec-Driven Development (SDD)**. Each phase introduces new capabilities while maintaining backward compatibility and architectural integrity.

| Phase | Feature | Status |
|-------|---------|--------|
| 001 | Core CRUD + Authentication | ✅ Complete |
| 002 | AI Chatbot (natural language) | ✅ Complete |
| 003 | Kubernetes Local Deployment | ✅ Complete |
| 004 | Advanced Task Features | ✅ Complete |
| 005 | Event-Driven Architecture | ✅ Complete |

---

## Key Features

### Core Task Management
- **CRUD operations** — create, read, update, delete tasks
- **Completion tracking** — toggle tasks complete/incomplete
- **User isolation** — JWT-authenticated, per-user data
- **Priority levels** — High, Medium, Low with visual indicators
- **Tags & categories** — flexible labeling and organization
- **Due dates & reminders** — browser notifications on deadline
- **Search, filter & sort** — full-text search, multi-field filtering

### Advanced Capabilities
- **AI chatbot** — manage tasks via natural language ("add buy milk due tomorrow, high priority")
- **Recurring tasks** — daily, weekly, monthly auto-generation via APScheduler
- **Real-time sync** — Server-Sent Events (SSE) push updates across browser tabs/devices
- **Event audit trail** — full history of every task state change
- **MCP integration** — AI agents use Model Context Protocol for structured tool access

### Architecture & Infrastructure
- **Fully containerized** — Docker + Docker Compose for local development
- **Kubernetes-ready** — Helm charts included for Minikube and cloud clusters
- **Event-driven** — Kafka-compatible streaming via Redpanda + Dapr pub/sub
- **Microservices** — six independently deployable services
- **Dapr runtime** — service invocation, pub/sub, state management, resilience
- **Observable** — structured logging, Prometheus-ready metrics, Grafana dashboards

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16 (App Router), TypeScript 5, Tailwind CSS 4 |
| **Backend API** | Python 3.13, FastAPI 0.115, SQLModel, asyncpg |
| **Database** | Neon Serverless PostgreSQL |
| **Migrations** | Alembic |
| **Authentication** | Better Auth (JWT), `@neondatabase/serverless` |
| **AI / Agents** | OpenAI Agents SDK, MCP SDK v1.26, ChatKit SDK v1.6 |
| **Messaging** | Redpanda (Kafka-compatible), Dapr pub/sub |
| **State / Cache** | Redis (Dapr state store) |
| **Containers** | Docker, Docker Compose |
| **Orchestration** | Kubernetes, Helm |
| **Service Mesh** | Dapr distributed runtime |
| **Task Scheduling** | APScheduler 3.x |

---

## Quick Start

### Prerequisites

```
Node.js 18+
Python 3.13+
Docker & Docker Compose
```

### 1. Clone and configure environment

```bash
git clone https://github.com/your-org/todo-app.git
cd todo-app
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
OPENAI_API_KEY=sk-...
BETTER_AUTH_SECRET=your-secret-here
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-secret-here
BETTER_AUTH_URL=http://localhost:3000
```

### 2. Run with Docker Compose

```bash
docker-compose up
```

This starts the backend API, frontend, MCP server, notification service, SSE gateway, Redpanda, and Redis.

Access the app at **http://localhost:3000**

### 3. Run manually (without Docker)

```bash
# Backend — install and migrate
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend — in a second terminal
cd frontend
npm install
npm run dev
```

---

## Kubernetes Deployment

### Local (Minikube)

```bash
# Set up Minikube with required addons
./scripts/minikube-setup.sh

# Build images into Minikube's Docker daemon
eval $(minikube docker-env)
docker build -f Dockerfile.frontend -t todo-frontend:latest .
docker build -f Dockerfile.backend  -t todo-backend:latest .

# Deploy with Helm
helm install todo-app ./chart

# Open in browser
minikube service todo-app-frontend
```

### Cloud

```bash
# Configure cloud credentials, then:
./scripts/build-and-deploy.sh
```

Refer to `specs/003-kubernetes-local/` for detailed Kubernetes architecture.

---

## Event-Driven Architecture

The app uses **Dapr** as the distributed runtime with **Redpanda** as the Kafka-compatible message broker.

### Pub/Sub Topics

| Topic | Publisher | Subscriber | Purpose |
|-------|-----------|------------|---------|
| `task-events` | Backend API | Notification Service | Audit trail, CRUD events |
| `reminders` | Backend API | Notification Service | Due date alerts |
| `task-updates` | Backend API | SSE Gateway | Real-time client sync |

### Dapr Components

| Component | Type | Backend |
|-----------|------|---------|
| `pubsub-redpanda` | Pub/Sub | Redpanda (Kafka) |
| `statestore-redis` | State Store | Redis |
| `secrets-kubernetes` | Secrets | K8s Secrets |

### Services

```
┌─────────────┐     HTTP/SSE      ┌──────────────────┐
│  Next.js 16 │◄──────────────────│  SSE Gateway     │
│  (Frontend) │                   │  (FastAPI)       │
└──────┬──────┘                   └────────┬─────────┘
       │ REST                               │ Dapr sub
       ▼                                   │
┌─────────────┐    Dapr pub/sub   ┌────────┴─────────┐
│  FastAPI    │──────────────────►│  Redpanda        │
│  Backend    │                   │  (Kafka broker)  │
└──────┬──────┘                   └────────┬─────────┘
       │ MCP                               │ Dapr sub
       ▼                                   ▼
┌─────────────┐               ┌──────────────────────┐
│  MCP Server │               │  Notification Service │
│  (AI tools) │               │  (FastAPI)            │
└─────────────┘               └──────────────────────┘
```

---

## Project Structure

```
todo-app/
├── frontend/                  # Next.js 16 application
│   └── src/
│       ├── app/               # App Router pages & layouts
│       └── components/        # Reusable UI components
├── backend/
│   ├── app/                   # FastAPI application
│   │   ├── routes/            # HTTP route handlers
│   │   ├── events/            # Event publisher & schemas
│   │   ├── chat/              # AI chatbot integration
│   │   └── mcp/               # MCP tool definitions
│   ├── services/
│   │   ├── notification/      # Dapr subscriber — handles alerts
│   │   └── sse_gateway/       # SSE push to browser clients
│   ├── alembic/               # Database migrations
│   └── tests/                 # pytest test suite
├── chart/                     # Helm chart (K8s deployment)
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── dapr/                      # Dapr configuration
│   ├── components/            # State store, pub/sub, secrets
│   ├── subscriptions/         # Topic subscription configs
│   └── resiliency.yaml
├── specs/                     # Spec-Driven Development artifacts
│   ├── 001-todo-crud/
│   ├── 002-ai-chatbot/
│   ├── 003-kubernetes-local/
│   ├── 004-advanced-features/
│   └── 005-event-driven/
├── scripts/                   # Deployment and setup scripts
├── Dockerfile.backend
├── Dockerfile.frontend
├── Dockerfile.mcp
└── docker-compose.yml
```

---

## API Reference

The backend exposes a REST API at `http://localhost:8000`. Interactive docs available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/sign-up` | Register a new user |
| `POST` | `/auth/sign-in` | Authenticate and receive JWT |
| `GET` | `/todos` | List tasks (filterable, sortable) |
| `POST` | `/todos` | Create a new task |
| `PATCH` | `/todos/{id}` | Update task fields |
| `DELETE` | `/todos/{id}` | Delete a task |
| `POST` | `/chat` | Send natural language message |
| `GET` | `/notifications` | SSE stream for real-time updates |
| `GET` | `/events/{task_id}` | Task event history |

---

## Development

### Running Tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm test
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

### Event Infrastructure (Local)

```bash
# Start Redpanda + Redis via Docker
./scripts/setup-event-infra.sh

# Start backend with Dapr sidecar
dapr run --app-id todo-backend --app-port 8000 \
  --components-path ./dapr/components \
  -- uvicorn app.main:app --port 8000
```

---

## Spec-Driven Development

This project is built using **Spec-Driven Development (SDD)** — each feature starts with a written specification before any code is written.

```
specs/<feature>/
├── spec.md           # Requirements and acceptance criteria
├── plan.md           # Architecture decisions and design
├── tasks.md          # Ordered, testable implementation tasks
├── data-model.md     # Schema design
├── research.md       # Technology evaluation notes
└── contracts/
    └── api.yaml      # OpenAPI contract
```

### Reusable Development Skills

Six reusable AI-assisted development skills are included in `.claude/skills/`:

| Skill | Purpose |
|-------|---------|
| `mcp-server-generator` | Scaffold MCP tool servers |
| `docker-containerization` | Dockerize services with best practices |
| `kubernetes-helm-charts` | Generate K8s manifests and Helm charts |
| `dapr-configuration` | Configure Dapr components and subscriptions |
| `cloud-deployment-blueprint` | Multi-cloud deployment patterns |
| `observability-monitoring` | Prometheus, Grafana, alerting setup |

---

## Contributing

Contributions are welcome. Please follow the existing patterns:

1. **Fork** the repository and create a feature branch
2. **Write a spec** in `specs/<feature>/spec.md` before coding
3. **Follow the task structure** — keep changes small and testable
4. **Add tests** for all new routes and business logic
5. **Open a pull request** with a description referencing the spec

---

## License

[MIT License](LICENSE) — free to use, modify, and distribute.

# Quickstart — Todo CRUD Application

**Feature**: 001-todo-crud
**Date**: 2026-02-08

## Prerequisites

- Node.js 20.9+ (for Next.js 16)
- Python 3.13+ (for FastAPI)
- Neon PostgreSQL account (free tier: https://neon.tech)
- Git

## 1. Clone and Setup

```bash
git clone <repo-url>
cd hackathon-todo
git checkout 001-todo-crud
```

## 2. Database Setup (Neon)

1. Create a project at https://console.neon.tech
2. Copy the connection string from the dashboard
3. Format: `postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`

## 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your Neon connection string and Better Auth URL
```

### Backend Environment Variables

```env
# .env
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
BETTER_AUTH_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
DEBUG=true
```

### Run Migrations

```bash
alembic upgrade head
```

### Start Backend

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

## 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your settings
```

### Frontend Environment Variables

```env
# .env.local
BETTER_AUTH_SECRET=<generate-a-random-secret>
BETTER_AUTH_URL=http://localhost:3000
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
NEXT_PUBLIC_API_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

### Start Frontend

```bash
npm run dev
```

App available at: http://localhost:3000

## 5. Development Workflow

```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Database migrations (as needed)
cd backend && source .venv/bin/activate && alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 6. Verify Setup

1. Open http://localhost:3000 — should see login/signup page
2. Register a new account
3. Create a task — should appear in the list
4. Open http://localhost:8000/docs — should see Swagger API docs
5. Try an unauthenticated API call — should get 401

## Key URLs

| Service       | URL                        | Purpose              |
| ------------- | -------------------------- | -------------------- |
| Frontend      | http://localhost:3000       | Next.js application  |
| Backend API   | http://localhost:8000       | FastAPI server       |
| API Docs      | http://localhost:8000/docs  | Swagger UI           |
| Auth Endpoints| http://localhost:3000/api/auth/* | Better Auth routes |
| Neon Console  | https://console.neon.tech  | Database management  |

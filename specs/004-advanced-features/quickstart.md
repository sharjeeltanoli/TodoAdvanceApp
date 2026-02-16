# Quickstart: Enhanced Task Management (004-advanced-features)

**Date**: 2026-02-16
**Branch**: `004-advanced-features`

## Prerequisites

- Node.js 18+ and npm
- Python 3.13+ and pip
- Access to Neon PostgreSQL database (DATABASE_URL in .env)
- Backend and frontend from 001-todo-crud running

## Setup Steps

### 1. Switch to feature branch

```bash
git checkout 004-advanced-features
```

### 2. Backend dependencies

```bash
cd backend
pip install apscheduler date-fns  # New dependency for recurring task scheduler
pip install -r requirements.txt   # If requirements.txt is updated
```

### 3. Run database migration

```bash
cd backend
alembic upgrade head  # Applies 004_add_advanced_fields migration
```

This adds columns (`priority`, `tags`, `due_date`, `recurrence_pattern`, `reminder_minutes`, `parent_task_id`) to the `task` table. Existing tasks automatically get defaults (`priority='medium'`, `tags='[]'`).

### 4. Frontend dependencies

```bash
cd frontend
npm install date-fns  # Date formatting utilities
```

### 5. Start services

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: MCP Server (optional)
cd backend
uvicorn mcp_server.server:app --host 0.0.0.0 --port 8001
```

### 6. Verify

1. Open http://localhost:3000/dashboard
2. Create a task — should see priority selector, tag input, date picker
3. Verify existing tasks still display correctly (backward compatibility)
4. Try search/filter/sort controls

## Key Files Modified

| File | Change |
| ---- | ------ |
| `backend/app/models.py` | Extended Task model + new Pydantic schemas |
| `backend/app/routes/todos.py` | Search/filter/sort params + new endpoints |
| `backend/app/scheduler.py` | NEW: Recurring task scheduler |
| `backend/alembic/versions/004_*.py` | NEW: Migration for new columns |
| `backend/mcp_server/server.py` | Extended MCP tools |
| `frontend/src/components/tasks/*` | Modified task components |
| `frontend/src/components/ui/*` | NEW: priority-badge, tag-input, date-picker, filter-bar, sort-select, search-input |
| `frontend/src/lib/notifications.ts` | NEW: Browser notification wrapper |
| `frontend/src/app/dashboard/actions.ts` | Extended server actions |

## Rollback

```bash
cd backend
alembic downgrade -1  # Reverts 004 migration (drops new columns)
git checkout main     # Return to main branch
```

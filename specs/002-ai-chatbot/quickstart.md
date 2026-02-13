# Quickstart: AI-Powered Todo Chatbot

**Feature**: 002-ai-chatbot
**Prerequisites**: Phase 2 (001-todo-crud) fully functional

## Prerequisites

- Node.js 20.9+ and npm
- Python 3.13+ with pip
- Neon PostgreSQL database (same as Phase 2)
- OpenAI API key with Agents SDK access
- Phase 2 application running (user registration, task CRUD working)

## 1. Environment Setup

Add new variables to `backend/.env`:

```env
# Existing (from Phase 2)
DATABASE_URL=postgresql://...@....neon.tech/neondb?sslmode=require
BETTER_AUTH_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000

# New for Phase 3
OPENAI_API_KEY=sk-...
MCP_SERVER_URL=http://localhost:8001/mcp
MCP_SERVER_PORT=8001
```

## 2. Install Backend Dependencies

```bash
cd backend
pip install openai-chatkit openai-agents "mcp[cli]"
```

Or if using the project's pyproject.toml (after it's updated):

```bash
cd backend
pip install -e ".[dev]"
```

## 3. Install Frontend Dependencies

```bash
cd frontend
npm install @openai/chatkit-react
```

## 4. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This creates the `conversation` and `message` tables.

## 5. Start All Services

Open 3 terminals:

**Terminal 1 — Backend API (port 8000)**:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — MCP Server (port 8001)**:
```bash
cd backend
python -m app.mcp.server
```

**Terminal 3 — Frontend (port 3000)**:
```bash
cd frontend
npm run dev
```

## 6. Verify

### MCP Server Health
```bash
# Optional: MCP Inspector for interactive tool testing
cd backend && mcp dev app/mcp/server.py
```

### Chat Interface
1. Open http://localhost:3000/login
2. Log in with existing credentials
3. Navigate to http://localhost:3000/dashboard/chat
4. Type "Hello" — expect an AI response
5. Type "Add buy groceries to my list" — expect task creation confirmation
6. Navigate to http://localhost:3000/dashboard — verify task appears

## Key URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Next.js app |
| Chat page | http://localhost:3000/dashboard/chat | AI chatbot |
| Task dashboard | http://localhost:3000/dashboard | Phase 2 UI |
| Backend API | http://localhost:8000 | FastAPI |
| ChatKit endpoint | http://localhost:8000/chatkit | ChatKit SDK |
| MCP Server | http://localhost:8001/mcp | MCP tools |
| MCP Inspector | http://localhost:5173 | Dev tool (optional) |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "OPENAI_API_KEY not set" | Add `OPENAI_API_KEY=sk-...` to `backend/.env` |
| MCP server won't start | Check port 8001 is free: `lsof -i :8001` |
| "Invalid token" in chat | Ensure you're logged in and session is valid |
| ChatKit shows blank | Check browser console; verify `/chatkit` endpoint returns |
| Agent can't find tools | Verify MCP server is running on port 8001 |
| Migration fails | Run `alembic downgrade base` then `alembic upgrade head` |

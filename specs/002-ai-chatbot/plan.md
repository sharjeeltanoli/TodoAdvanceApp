# Implementation Plan: AI-Powered Todo Chatbot

**Branch**: `002-ai-chatbot` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-ai-chatbot/spec.md`

## Summary

Add a conversational AI interface to the existing todo application. Users interact through natural language to create, view, complete, update, and delete tasks. The architecture introduces three new components: (1) an MCP server exposing task operations as tools, (2) an OpenAI Agent that interprets user intent and calls MCP tools, and (3) a ChatKit-powered chat UI with persistent conversation history stored in the database.

## Technical Context

**Language/Version**: Python 3.13 (backend + MCP + agent), TypeScript 5.x (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.115.8, SQLModel 0.0.22, asyncpg 0.30.0, httpx 0.28.1
- New: `openai-chatkit` (ChatKit Python SDK), `openai-agents` (Agents SDK), `mcp[cli]` (MCP SDK v1.2.0+)
- Frontend: Next.js 16.1.6, React 19.2.3
- New: `@openai/chatkit-react`
**Storage**: Neon Serverless PostgreSQL (shared — adds `conversation` + `message` tables)
**Testing**: pytest + pytest-asyncio (backend), Vitest (frontend)
**Target Platform**: Linux server (dev), Docker (Phase 4)
**Project Type**: Web application (monorepo: `frontend/` + `backend/`)
**Performance Goals**: First response token < 5s, full tool round-trip < 8s (SC-001, SC-002)
**Constraints**: User isolation on every layer (Constitution V), MCP-only AI access (Constitution VI)
**Scale/Scope**: Single-user concurrent chat, < 500 tasks per user, < 100 conversations per user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Development | PASS | spec.md, plan.md, research.md, data-model.md, contracts/ created before code |
| II. Monorepo Structure | PASS | All changes within existing `frontend/` and `backend/` directories |
| III. Stateless Services | PASS | Conversations stored in Neon DB; MCP server and agent are stateless per-request |
| IV. Event-Driven Architecture | N/A | No async inter-service communication needed for chat (synchronous request-response) |
| V. User Isolation | PASS | 4-layer isolation: proxy → ChatKit context → Agent → MCP tool auth_token → DB query filter |
| VI. MCP Protocol | PASS | Agent accesses tasks exclusively via MCP tools; no direct DB access from AI |

**Security Requirements**:
- Bearer token required on `/chatkit` endpoint ✓
- ChatKit Store filters all queries by `user_id` from context ✓
- MCP tools validate auth_token independently ✓
- No hardcoded secrets (OPENAI_API_KEY, DATABASE_URL in .env) ✓
- CORS extended to allow ChatKit frontend origin ✓

## Project Structure

### Documentation (this feature)

```text
specs/002-ai-chatbot/
├── plan.md                         # This file
├── spec.md                         # Feature specification
├── research.md                     # Technology research decisions
├── data-model.md                   # Database schema changes
├── quickstart.md                   # Setup and run instructions
├── contracts/
│   ├── api.yaml                    # REST + ChatKit endpoint OpenAPI
│   └── mcp-tools.yaml             # MCP tool definitions
├── checklists/
│   └── requirements.md            # Spec quality checklist
└── tasks.md                        # Implementation tasks (via /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                     # FastAPI app — add /chatkit route, CORS update
│   ├── config.py                   # Add OPENAI_API_KEY, MCP_SERVER_URL settings
│   ├── database.py                 # Unchanged (shared engine)
│   ├── dependencies.py             # Unchanged (existing auth helper)
│   ├── models.py                   # Add Conversation + Message SQLModels
│   ├── routes/
│   │   ├── todos.py                # Unchanged (Phase 2 REST API)
│   │   ├── chat.py                 # ChatKit endpoint handler + conversation REST
│   │   └── __init__.py
│   ├── chat/
│   │   ├── __init__.py
│   │   ├── server.py               # ChatKitServer subclass (respond method)
│   │   ├── store.py                # Database-backed ChatKit Store
│   │   └── agent.py                # Agent configuration + MCP connection
│   └── mcp/
│       ├── __init__.py
│       ├── server.py               # MCPServer instance, lifespan, auth helper
│       └── tools/
│           ├── __init__.py
│           └── tasks.py            # 6 MCP tool implementations
├── alembic/
│   └── versions/
│       ├── 001_create_task_table.py           # Existing
│       └── 002_create_conversation_and_message_tables.py  # New
├── pyproject.toml                  # Add openai-chatkit, openai-agents, mcp[cli]
├── .env.example                    # Add OPENAI_API_KEY, MCP_SERVER_URL
└── tests/
    ├── test_mcp_tools.py           # MCP tool unit tests
    └── test_chat.py                # Chat endpoint integration tests

frontend/
├── src/
│   ├── app/
│   │   └── dashboard/
│   │       ├── chat/
│   │       │   └── page.tsx        # Chat page with ChatKit component
│   │       ├── layout.tsx          # Update nav — add Chat link
│   │       └── page.tsx            # Unchanged (task dashboard)
│   ├── components/
│   │   └── chat/
│   │       └── chat-panel.tsx      # ChatKit wrapper with auth
│   ├── lib/
│   │   ├── auth.ts                 # Unchanged
│   │   ├── auth-client.ts          # Unchanged
│   │   └── api.ts                  # Unchanged
│   └── proxy.ts                    # Unchanged (chat page is protected)
├── package.json                    # Add @openai/chatkit-react
└── tests/
    └── chat.test.tsx               # Chat component tests
```

**Structure Decision**: Extends the existing monorepo. New `backend/app/chat/` package encapsulates ChatKit server, store, and agent logic. New `backend/app/mcp/` package is the standalone MCP server. Frontend adds a chat page under the existing dashboard layout.

## Architecture Overview

### Request Flow

```
┌──────────────────┐     POST /chatkit      ┌──────────────────────┐
│  ChatKit React   │ ─────────────────────► │  FastAPI Backend     │
│  (@openai/       │ ◄─────────────────────  │                      │
│   chatkit-react) │    SSE stream           │  ┌────────────────┐  │
│                  │                         │  │ ChatKitServer   │  │
│  useChatKit({    │                         │  │  .respond()     │  │
│   api.url,       │                         │  │                 │  │
│   api.headers    │                         │  │  ┌───────────┐ │  │
│  })              │                         │  │  │ DB Store  │ │  │
└──────────────────┘                         │  │  │ (threads, │ │  │
                                             │  │  │  items)   │ │  │
                                             │  │  └───────────┘ │  │
                                             │  │                 │  │
                                             │  │  ┌───────────┐ │  │
                                             │  │  │ Agent     │ │  │
                                             │  │  │ (OpenAI)  │ │  │
                                             │  │  └─────┬─────┘ │  │
                                             │  └───────│────────┘  │
                                             └──────────│───────────┘
                                                        │
                                              MCP call  │  streamable-http
                                                        ▼
                                             ┌──────────────────────┐
                                             │   MCP Server (:8001) │
                                             │                      │
                                             │  Tools:              │
                                             │  - add_task          │
                                             │  - list_tasks        │
                                             │  - complete_task     │
                                             │  - update_task       │
                                             │  - delete_task       │
                                             │  - task_summary      │
                                             │                      │
                                             │  ┌────────────────┐  │
                                             │  │ Neon PostgreSQL │  │
                                             │  │ (task table)    │  │
                                             │  └────────────────┘  │
                                             └──────────────────────┘
```

### Authentication Flow

```
1. User logs in (Phase 2) → Better Auth issues session token (cookie + Bearer)
2. ChatKit React reads token from auth-client → sets Authorization header
3. FastAPI /chatkit endpoint extracts Bearer token → validates via Better Auth
4. Validated user_id + auth_token passed as ChatKit context dict
5. ChatKit Store uses context["user_id"] to filter conversation/message queries
6. Agent receives context["auth_token"] → passes to MCP tools as parameter
7. MCP tools independently validate auth_token → extract user_id → filter DB queries
```

**4-layer isolation**:
- Layer 1: `proxy.ts` — cookie check, redirect unauthenticated
- Layer 2: FastAPI endpoint — Bearer token validation, user_id extraction
- Layer 3: ChatKit Store — all queries filtered by `context["user_id"]`
- Layer 4: MCP tools — independent token validation, DB queries by user_id

### Component Details

#### 1. MCP Server (`backend/app/mcp/`)

Standalone process on port 8001. Uses `MCPServer` from the official MCP SDK with `streamable-http` transport.

**Lifespan**: Manages async SQLAlchemy engine + httpx client for auth validation.

**Tools** (6 total):

| Tool | Description | Maps to Phase 2 endpoint |
|------|-------------|--------------------------|
| `add_task` | Create task with title + description | POST /api/todos |
| `list_tasks` | List user's tasks with optional filter | GET /api/todos |
| `complete_task` | Toggle completion status | PATCH /api/todos/{id}/complete |
| `update_task` | Update title and/or description | PUT /api/todos/{id} |
| `delete_task` | Permanently delete a task | DELETE /api/todos/{id} |
| `task_summary` | Get total/completed/pending counts | (new — aggregate query) |

**Auth pattern**: Token passthrough. Every tool accepts `auth_token` as a parameter. The MCP server validates the token via Better Auth's `/api/auth/get-session` endpoint and extracts `user_id` for query scoping.

**Reference**: `.claude/skills/mcp-server-generator/` — templates and example.

#### 2. ChatKit Backend (`backend/app/chat/`)

Integrates into the existing FastAPI app on port 8000.

**server.py** — `TodoChatKitServer(ChatKitServer[dict])`:
- `respond()` loads thread history via Store
- Converts thread items to agent input via `simple_to_agent_input()`
- Runs agent with `Runner.run_streamed()`
- Yields `ThreadStreamEvent`s via `stream_agent_response()`

**store.py** — `DatabaseChatKitStore(Store[dict])`:
- Wraps async SQLAlchemy sessions
- Maps `ThreadMetadata` ↔ `Conversation` model
- Maps `ThreadItem` ↔ `Message` model
- All queries filter by `context["user_id"]`
- Implements pagination with cursor-based `Page` objects

**agent.py** — Agent configuration:
- Creates `MCPServerStreamableHttp` connection to MCP server on port 8001
- Passes `auth_token` from context in MCP request headers
- Configures `Agent(name, instructions, model, mcp_servers=[mcp])`
- System instructions constrain agent to task management domain
- `cache_tools_list=True` for performance

#### 3. ChatKit Frontend (`frontend/src/`)

**chat-panel.tsx** — Client component:
```tsx
const chatkit = useChatKit({
  api: {
    url: `${BACKEND_URL}/chatkit`,
    domainKey: "todo-app",
    headers: { Authorization: `Bearer ${sessionToken}` },
  },
});
return <ChatKit control={chatkit.control} className="h-full" />;
```

**chat/page.tsx** — Dashboard subpage at `/dashboard/chat`:
- Gets session token from auth-client
- Renders ChatPanel component
- Protected by existing proxy.ts auth check

**layout.tsx** — Updated dashboard nav:
- Adds "Chat" link alongside existing dashboard page

#### 4. Database Changes

Two new tables via Alembic migration `002`:

- `conversation` (id, user_id, title, created_at, updated_at)
- `message` (id, conversation_id, role, content, created_at)

Details in [data-model.md](data-model.md).

Two new SQLModel classes in `backend/app/models.py`:

```python
class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Message(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", index=True)
    role: str = Field(max_length=20)  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Agent System Instructions

```text
You are a task management assistant. You help users manage their todo list
through natural language conversation.

Available actions:
- Add tasks: Create new tasks with a title and optional description
- List tasks: Show all tasks, or filter by pending/completed status
- Complete tasks: Mark tasks as done or undo completion
- Update tasks: Change a task's title or description
- Delete tasks: Permanently remove tasks (always confirm first)
- Summarize: Show task counts (total, completed, pending)

Behavior rules:
1. When a user asks to delete a task, ALWAYS ask for confirmation before
   executing the deletion.
2. When multiple tasks match a user's reference, list the matching tasks
   and ask which one they mean.
3. When the user's intent is unclear, ask a clarifying question.
4. Stay focused on task management. If asked about unrelated topics,
   politely redirect: "I'm your task assistant — I can help you add, view,
   update, complete, or delete tasks."
5. After performing an action, confirm what was done with specific details.
6. Format task lists clearly with completion status indicators.
```

### Environment Variables (New)

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for Agents SDK | `sk-...` |
| `MCP_SERVER_URL` | URL of the MCP server | `http://localhost:8001/mcp` |
| `MCP_SERVER_PORT` | Port for standalone MCP server | `8001` |

Added to `backend/app/config.py` as `Settings` fields with defaults.

### Error Handling

| Scenario | Handler | User-facing behavior |
|----------|---------|---------------------|
| AI service down | `ChatKitServer.respond()` try/catch | "I'm having trouble right now. Please try again." |
| MCP server down | Agent tool call fails | Agent receives error, tells user "I can't access your tasks right now." |
| Invalid auth token | FastAPI dependency | 401 JSON error before reaching ChatKit |
| Task not found | MCP tool ValueError | Agent tells user "I couldn't find that task." |
| Ambiguous task ref | Agent system instructions | Agent lists matching tasks, asks user to pick |
| Off-topic request | Agent system instructions | Agent redirects to task management |
| Empty message | Frontend validation | Disabled send button, validation hint |
| Message too long | Frontend validation | Character counter, disabled send at 4000 |

### Development Workflow

```
Terminal 1: Backend API        → cd backend && uvicorn app.main:app --reload --port 8000
Terminal 2: MCP Server         → cd backend && python -m app.mcp.server
Terminal 3: Frontend           → cd frontend && npm run dev
Terminal 4: MCP Inspector      → cd backend && mcp dev app/mcp/server.py  (optional)
```

**Order of implementation**:
1. Database migration (conversation + message tables)
2. SQLModel models (Conversation, Message)
3. MCP server + tools (standalone, testable with MCP Inspector)
4. ChatKit Store (database-backed, testable independently)
5. ChatKit Server + Agent integration
6. FastAPI /chatkit endpoint wiring
7. Frontend ChatKit component
8. Dashboard navigation update
9. Error handling + edge cases
10. End-to-end testing

## Complexity Tracking

No constitution violations. All principles satisfied without justification needed.

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP server architecture | Standalone (Pattern 1) | Clean process isolation, independent scaling, aligns with Constitution VI |
| MCP transport | streamable-http | Works with OpenAI Agents SDK `MCPServerStreamableHttp`, HTTP-native |
| Chat UI | OpenAI ChatKit (self-hosted) | Drop-in streaming chat component, thread management built-in |
| Agent framework | OpenAI Agents SDK | Native MCP support, auto tool discovery, streaming responses |
| Conversation persistence | ChatKit Store → PostgreSQL | Reuses existing Neon DB, consistent with Phase 2 data layer |
| Auth in MCP | Token passthrough | Simplest, reuses existing Better Auth validation, no new auth system |
| Agent model | gpt-4.1-mini | Good balance of capability and cost for task management |
| Chat page placement | /dashboard/chat | Protected by existing auth, consistent with dashboard layout |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI API rate limits or outages | Chat becomes unavailable | Error handling returns user-friendly message; task dashboard remains fully functional |
| MCP server process crash | Agent can't access tasks | Supervisor/restart policy; FastAPI catches error, returns graceful message |
| Token expiry during long chat session | Auth failure mid-conversation | ChatKit React refreshes token from auth-client on each request |
| Agent misinterprets user intent | Wrong task modified | Disambiguation instructions; confirmation for destructive actions |
| Large conversation history | Slow agent context loading | Limit to last 20 messages per thread (ChatKit Store `load_thread_items` limit) |

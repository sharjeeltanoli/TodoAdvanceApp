# Research: AI-Powered Todo Chatbot

**Feature**: 002-ai-chatbot
**Date**: 2026-02-10

## R-001: ChatKit Frontend Integration

**Decision**: Use `@openai/chatkit-react` with self-hosted Python backend via `openai-chatkit` SDK.

**Rationale**: ChatKit provides a production-ready conversational UI component with built-in streaming, thread management, and message rendering. The self-hosted backend approach gives full control over data persistence, auth, and agent orchestration without depending on OpenAI's hosted infrastructure.

**Alternatives considered**:
- Custom chat UI built from scratch — too much effort for streaming, thread management, message rendering
- Vercel AI SDK `useChat` — simpler but doesn't provide the rich widget/thread management that ChatKit offers
- OpenAI hosted ChatKit — would require external data storage and complicate user isolation

**Key findings**:
- Install: `npm install @openai/chatkit-react` (frontend), `pip install openai-chatkit` (backend)
- Frontend sends all requests to a single `/chatkit` endpoint
- `ChatKitServer.process()` handles internal routing (threads, messages, streaming)
- `useChatKit({ api: { url, domainKey } })` configures the React component
- Backend must implement `ChatKitServer.respond()` + `Store` (persistence layer)

## R-002: OpenAI Agents SDK with MCP Integration

**Decision**: Use `openai-agents` SDK with `MCPServerStreamableHttp` transport to connect the agent to our MCP tools server.

**Rationale**: The Agents SDK has native MCP support. The agent auto-discovers tools from the MCP server at startup, requiring zero manual tool registration. `MCPServerStreamableHttp` connects to our standalone MCP server over HTTP with auth headers.

**Alternatives considered**:
- Direct function tools on the Agent — would bypass MCP, violating Constitution Principle VI
- `MCPServerStdio` — requires subprocess management, not suitable for multi-user web service
- `HostedMCPTool` — requires publicly reachable MCP server, adds complexity for local dev

**Key findings**:
- Install: `pip install openai-agents`
- Agent constructor: `Agent(name, instructions, model, mcp_servers=[server])`
- Streaming: `Runner.run_streamed(agent, input_items, context=agent_context)`
- MCP connection: `MCPServerStreamableHttp(params={"url": "...", "headers": {...}})`
- Tools are auto-discovered via `list_tools()` — no manual registration needed
- `cache_tools_list=True` avoids re-fetching tool definitions on every request
- ChatKit integration: `chatkit.agents.stream_agent_response()` bridges agent output to ChatKit events

## R-003: MCP Server Architecture

**Decision**: Standalone MCP server process (Pattern 1 from our skill) running on port 8001 with `streamable-http` transport.

**Rationale**: Separating the MCP server from the FastAPI app provides clean process isolation, independent scaling, and alignment with Constitution Principle VI (MCP as the sole AI-to-app interface). The agent connects via HTTP, which works identically in local dev and production.

**Alternatives considered**:
- Mounted on FastAPI via `fastapi-mcp` — simpler but couples MCP lifecycle to the web app, makes it harder to scale independently
- Hybrid pattern — adds complexity without clear benefit at this stage

**Key findings**:
- Uses `MCPServer` class from `mcp` SDK (v1.2.0+)
- Lifespan manages async DB engine + httpx client for auth validation
- 5 core tools: `add_task`, `list_tasks`, `complete_task`, `update_task`, `delete_task`
- 1 utility tool: `task_summary` (counts for quick status)
- Auth: Token passthrough — agent passes user's Bearer token as tool parameter
- Each tool validates token via Better Auth `/api/auth/get-session`
- All queries filter by `user_id` for isolation
- Templates available at `.claude/skills/mcp-server-generator/`

## R-004: ChatKit Store (Conversation Persistence)

**Decision**: Implement a database-backed `Store` subclass using async SQLAlchemy, mapping ChatKit's `ThreadMetadata` to `conversation` table and `ThreadItem` to `message` table.

**Rationale**: ChatKit's `Store` abstract class defines the persistence interface. Implementing it with our existing async SQLAlchemy infrastructure keeps the stack consistent and stores conversation data in Neon PostgreSQL alongside tasks and users.

**Alternatives considered**:
- In-memory store (ChatKit's example) — data lost on restart, not suitable for production
- Redis-backed store — adds infrastructure dependency, overkill for conversation storage
- Separate SQLite file — breaks the single-database principle

**Key findings**:
- Store interface requires: `load_thread`, `save_thread`, `load_threads`, `load_thread_items`, `add_thread_item`, `save_item`, `load_item`, `delete_thread`, `delete_thread_item`
- Attachment methods can raise `NotImplementedError` (out of scope)
- Pagination via `Page(data, has_more, after)` — cursor-based
- Thread ↔ conversation, ThreadItem ↔ message mapping is straightforward
- Store receives `context: dict` on every call — we pass `{"user_id": "..."}` for isolation

## R-005: Authentication Flow for Chat

**Decision**: Extract Bearer token from ChatKit request headers, validate via Better Auth, and pass `user_id` through ChatKit context to all downstream operations (Store queries, MCP tool calls).

**Rationale**: Reuses the existing 3-layer auth pattern from Phase 2. ChatKit React sends the session token in a custom header. The FastAPI endpoint validates it before calling `server.process()`, passing the user_id in the context dict.

**Alternatives considered**:
- Cookie-based auth in ChatKit — ChatKit doesn't natively support cookie auth on self-hosted backends
- Service-level auth for MCP (agent has its own credentials) — adds complexity, requires separate auth system

**Key findings**:
- ChatKit React: configure `api.headers` to include `Authorization: Bearer <token>`
- FastAPI endpoint: extract token, validate, extract user_id, pass as `context={"user_id": user_id, "auth_token": token}`
- ChatKit Store: filter all thread/item queries by `context["user_id"]`
- MCP tools: agent passes `context["auth_token"]` as the `auth_token` parameter
- This ensures user isolation at every layer: ChatKit → Store → Agent → MCP → Database

## R-006: Agent System Instructions Design

**Decision**: Use a focused system prompt that constrains the agent to task management, defines available actions, and specifies disambiguation and confirmation behaviors.

**Rationale**: Clear instructions prevent the agent from going off-topic and ensure consistent behavior for destructive actions (delete confirmation), ambiguous references (disambiguation), and unknown intents (clarifying questions).

**Key findings**:
- System prompt should enumerate available actions (add, list, complete, update, delete, summarize)
- Must instruct agent to confirm before deletions
- Must instruct agent to disambiguate when multiple tasks match
- Must instruct agent to ask clarifying questions for unclear intent
- Must instruct agent to politely decline off-topic requests
- Keep prompt under 500 tokens to minimize overhead per request

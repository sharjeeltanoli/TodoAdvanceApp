# Tasks: AI-Powered Todo Chatbot

**Input**: Design documents from `/specs/002-ai-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Test tasks omitted. Manual verification via MCP Inspector and browser.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies, configure environment, create package directories

- [x] T001 [P] Add Phase 3 Python dependencies (openai-chatkit, openai-agents, mcp[cli]) to `backend/pyproject.toml`
- [x] T002 [P] Add `@openai/chatkit-react` to `frontend/package.json` and run `npm install`
- [x] T003 [P] Add OPENAI_API_KEY, MCP_SERVER_URL, MCP_SERVER_PORT to `backend/app/config.py` Settings class and update `backend/.env.example`
- [x] T004 [P] Create package directories: `backend/app/mcp/`, `backend/app/mcp/tools/`, `backend/app/chat/` with `__init__.py` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema, models, MCP server scaffold, ChatKit Store, and Agent configuration

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Add Conversation and Message SQLModel classes to `backend/app/models.py` per data-model.md schema
- [x] T006 Create Alembic migration `backend/alembic/versions/002_create_conversation_and_message_tables.py` with conversation table (id, user_id, title, created_at, updated_at), message table (id, conversation_id, role, content, created_at), indexes, and FK cascades per data-model.md
- [x] T007 Run Alembic migration to create tables: `cd backend && alembic upgrade head`
- [x] T008 [P] Create MCP server scaffold in `backend/app/mcp/server.py` — FastMCP instance with lifespan (async engine + httpx client), validate_token helper, success_json helper, streamable-http transport config. Reference `.claude/skills/mcp-server-generator/templates/mcp-server-template.py`
- [x] T009 [P] Create database-backed ChatKit Store in `backend/app/chat/store.py` — implement Store[dict] with all required methods (load_thread, save_thread, load_threads, load_thread_items, add_thread_item, save_item, load_item, delete_thread, delete_thread_item) mapping ThreadMetadata↔Conversation and ThreadItem↔Message. All queries filter by context["user_id"]. Use async SQLAlchemy session from `backend/app/database.py`
- [x] T010 [P] Create Agent configuration in `backend/app/chat/agent.py` — function that creates MCPServerStreamableHttp connection to MCP_SERVER_URL, configures Agent with name="Todo Assistant", model="gpt-4.1-mini", system instructions from plan.md, mcp_servers=[mcp], cache_tools_list=True

**Checkpoint**: Foundation ready — database has conversation/message tables, MCP server scaffold runs, ChatKit Store persists to DB, Agent config exists

---

## Phase 3: User Story 1 — Send a Message and Receive a Response (Priority: P1) MVP

**Goal**: Authenticated user can open chat, type a message, and receive a streamed AI response

**Independent Test**: Log in → open /dashboard/chat → type "Hello" → verify AI response appears with streaming

### Implementation for User Story 1

- [x] T011 [US1] Create ChatKitServer subclass in `backend/app/chat/server.py` — TodoChatKitServer(ChatKitServer[dict]) with respond() method that loads thread items via Store, converts to agent input with simple_to_agent_input(), runs agent with Runner.run_streamed(), yields events via stream_agent_response(). Include try/except for AI service errors returning user-friendly message
- [x] T012 [US1] Create ChatKit route handler in `backend/app/routes/chat.py` — POST /chatkit endpoint that extracts Bearer token from Authorization header, validates via get_current_user dependency, passes context={"user_id": user_id, "auth_token": token} to server.process(), returns StreamingResponse for SSE or Response for JSON
- [x] T013 [US1] Register chat routes in `backend/app/main.py` — import and include chat router, ensure CORS allows ChatKit requests
- [x] T014 [P] [US1] Create ChatKit wrapper component in `frontend/src/components/chat/chat-panel.tsx` — client component using useChatKit hook with api.url pointing to BACKEND_URL/chatkit, api.headers with Authorization Bearer token from authClient session. Render ChatKit control with full-height styling
- [x] T015 [P] [US1] Create chat page at `frontend/src/app/dashboard/chat/page.tsx` — get session token, render ChatPanel component. Page is protected by existing proxy.ts
- [x] T016 [US1] Update dashboard navigation in `frontend/src/app/dashboard/layout.tsx` — add "Chat" link/button to nav bar alongside existing "Todo App" title and "Log Out" button

**Checkpoint**: User can navigate to /dashboard/chat, send "Hello", receive streamed AI response. Chat page is auth-protected.

---

## Phase 4: User Story 2 — Create a Task via Natural Language (Priority: P1)

**Goal**: User says "Add buy groceries to my list" → AI creates task via MCP tool → confirms in chat

**Independent Test**: Type "Add buy groceries to my list" → verify task appears in chat confirmation AND /dashboard task list

**Depends on**: Phase 2 (MCP server scaffold), Phase 3 (working chat)

### Implementation for User Story 2

- [x] T017 [US2] Implement add_task MCP tool in `backend/app/mcp/tools/tasks.py` — @mcp.tool() decorator, accepts title (str, required), description (str, default=""), auth_token (str, required). Validates token, creates Task in DB with user_id, returns task dict. Reference `.claude/skills/mcp-server-generator/examples/todo-mcp-example.py` and `specs/002-ai-chatbot/contracts/mcp-tools.yaml`
- [x] T018 [US2] Register task tools module in `backend/app/mcp/server.py` — import tasks module so @mcp.tool decorators register at startup
- [x] T019 [US2] Verify add_task tool works via MCP Inspector: `cd backend && mcp dev app/mcp/server.py` — call add_task with test auth_token, confirm task appears in database

**Checkpoint**: User can create tasks via natural language. Created tasks visible in Phase 2 dashboard.

---

## Phase 5: User Story 3 — View Tasks via Natural Language (Priority: P1)

**Goal**: User says "Show my tasks" → AI lists tasks via MCP tools → presents formatted list in chat

**Independent Test**: Create tasks via dashboard → ask "Show my tasks" in chat → verify all tasks listed with correct status

**Depends on**: Phase 2 (MCP server scaffold), Phase 3 (working chat)

### Implementation for User Story 3

- [x] T020 [P] [US3] Implement list_tasks MCP tool in `backend/app/mcp/tools/tasks.py` — accepts auth_token (str, required), completed (bool|None, default=None). Validates token, queries tasks filtered by user_id and optional completed status, returns array of task dicts sorted by created_at DESC
- [x] T021 [P] [US3] Implement task_summary MCP tool in `backend/app/mcp/tools/tasks.py` — accepts auth_token (str, required). Returns {total, completed, pending} counts using SQL aggregate with FILTER
- [x] T022 [US3] Verify list_tasks and task_summary tools via MCP Inspector — create test tasks, call list_tasks with/without completed filter, call task_summary, confirm correct results

**Checkpoint**: User can ask "Show my tasks", "Show pending tasks", "How many tasks do I have?" and get correct formatted responses.

---

## Phase 6: User Story 4 — Complete a Task via Natural Language (Priority: P2)

**Goal**: User says "Mark buy groceries as done" → AI identifies task, toggles completion via MCP tool → confirms

**Independent Test**: Create a task → say "Mark [task] as done" → verify status change in chat AND dashboard

**Depends on**: Phase 5 (list_tasks needed for disambiguation)

### Implementation for User Story 4

- [x] T023 [US4] Implement complete_task MCP tool in `backend/app/mcp/tools/tasks.py` — accepts task_id (str, required), auth_token (str, required). Validates token, finds task by id+user_id, toggles completed boolean, updates updated_at, returns updated task dict. Raises ValueError if not found
- [x] T024 [US4] Verify complete_task tool via MCP Inspector — create task, toggle completion, toggle back, verify state changes

**Checkpoint**: User can complete/uncomplete tasks via chat. Agent disambiguates when multiple tasks match (via system instructions + list_tasks).

---

## Phase 7: User Story 5 — Update a Task via Natural Language (Priority: P2)

**Goal**: User says "Rename buy groceries to buy organic groceries" → AI updates task title via MCP tool → confirms

**Independent Test**: Create a task → say "Rename [task] to [new name]" → verify change in dashboard

**Depends on**: Phase 5 (list_tasks needed for disambiguation)

### Implementation for User Story 5

- [x] T025 [US5] Implement update_task MCP tool in `backend/app/mcp/tools/tasks.py` — accepts task_id (str, required), auth_token (str, required), title (str|None), description (str|None). Validates token, finds task by id+user_id, updates only provided fields, updates updated_at, returns updated task dict. Raises ValueError if not found. Validates title length 1-255, description max 2000
- [x] T026 [US5] Verify update_task tool via MCP Inspector — update title, update description, update both, verify changes persist

**Checkpoint**: User can rename tasks and update descriptions via chat.

---

## Phase 8: User Story 6 — Delete a Task via Natural Language (Priority: P3)

**Goal**: User says "Delete buy groceries" → AI asks confirmation → user confirms → task deleted via MCP tool

**Independent Test**: Create a task → say "Delete [task]" → confirm → verify task removed from dashboard

**Depends on**: Phase 5 (list_tasks needed for disambiguation)

### Implementation for User Story 6

- [x] T027 [US6] Implement delete_task MCP tool in `backend/app/mcp/tools/tasks.py` — accepts task_id (str, required), auth_token (str, required). Validates token, finds task by id+user_id, deletes from DB, returns {deleted: task_id}. Raises ValueError if not found. Agent system instructions handle confirmation flow (not the tool)
- [x] T028 [US6] Verify delete_task tool via MCP Inspector — create task, delete it, confirm it's gone from DB

**Checkpoint**: Full CRUD via natural language complete. Agent confirms before deleting (handled by system instructions).

---

## Phase 9: User Story 7 — Conversation History Persistence (Priority: P2)

**Goal**: User returns to chat → sees previous messages. Can start new conversation.

**Independent Test**: Have a conversation → navigate to /dashboard → return to /dashboard/chat → verify messages persist

**Depends on**: Phase 3 (working chat with Store)

### Implementation for User Story 7

- [x] T029 [US7] Add conversation list REST endpoint in `backend/app/routes/chat.py` — GET /api/conversations returns paginated list of user's conversations (newest first), DELETE /api/conversations/{id} deletes a conversation with cascade. Both filter by authenticated user_id
- [x] T030 [US7] Verify conversation persistence — send messages in chat, navigate away, return, confirm messages are loaded from DB. Check that conversation.updated_at is updated on each message
- [x] T031 [US7] Verify user isolation — log in as two different users, send messages, verify each user only sees their own conversations in the Store. Cross-user conversation IDs return 404

**Checkpoint**: Conversations persist across page loads. User isolation enforced. Previous messages displayed on return.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, input validation, responsive design, edge cases from spec

- [x] T032 [P] Add error handling for AI service unavailability in `backend/app/chat/server.py` — wrap respond() agent call in try/except, yield error ThreadStreamEvent with user-friendly message "I'm having trouble right now. Please try again in a moment." (FR-015, SC-007)
- [x] T033 [P] Add error handling for MCP server unavailability in `backend/app/chat/agent.py` — handle MCPServerStreamableHttp connection failures gracefully, agent should tell user "I can't access your tasks right now"
- [x] T034 [P] Add frontend input validation in `frontend/src/components/chat/chat-panel.tsx` — prevent empty/whitespace-only messages (FR-016), add 4000 character limit with character count indicator, disable send while AI is responding (FR-017)
- [x] T035 [P] Ensure chat interface is responsive 375px–1920px in `frontend/src/app/dashboard/chat/page.tsx` — ChatKit component should fill available space, test on mobile and desktop viewports (SC-006)
- [x] T036 [P] [US1] Implement loading indicator in `frontend/src/components/chat/chat-panel.tsx` — show "Thinking..." state while the agent processes the user's message, display a spinner component during streaming, hide when first response token arrives. Acceptance: user sees visual feedback immediately after sending a message (FR-019)
- [x] T037 [P] [US7] Add "New conversation" button in `frontend/src/app/dashboard/chat/page.tsx` — button in chat layout header that creates a new conversation in the DB (via ChatKit thread creation), clears the chat panel, and starts a fresh thread. Acceptance: user can start a fresh conversation while previous conversation is preserved (FR-011)
- [x] T038 Update `specs/002-ai-chatbot/quickstart.md` with final verified commands and any corrections discovered during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately. All tasks [P] run in parallel.
- **Foundational (Phase 2)**: Depends on Phase 1. T005→T006→T007 sequential (models→migration→run). T008, T009, T010 [P] in parallel.
- **US1 (Phase 3)**: Depends on Phase 2. T011→T012→T013 sequential (server→route→register). T014, T015 [P] frontend in parallel. T016 after T015.
- **US2 (Phase 4)**: Depends on Phase 2 (T008) + Phase 3 (working chat). T017→T018→T019 sequential.
- **US3 (Phase 5)**: Depends on Phase 2 (T008). T020, T021 [P] parallel. T022 after both.
- **US4 (Phase 6)**: Depends on Phase 5 (list_tasks for disambiguation). T023→T024 sequential.
- **US5 (Phase 7)**: Depends on Phase 5 (list_tasks for disambiguation). T025→T026 sequential.
- **US6 (Phase 8)**: Depends on Phase 5 (list_tasks for disambiguation). T027→T028 sequential.
- **US7 (Phase 9)**: Depends on Phase 3 (working chat). T029→T030→T031 sequential.
- **Polish (Phase 10)**: Depends on Phases 3–9. T032–T037 [P] parallel. T038 after all others.

### User Story Dependencies

```
Phase 1 (Setup) ─────► Phase 2 (Foundational) ─────┬──► Phase 3 (US1: Chat Loop) ─────┬──► Phase 4 (US2: Create) ──► Phase 10
                                                     │                                   ├──► Phase 5 (US3: View) ───┬──► Phase 6 (US4: Complete)
                                                     │                                   │                           ├──► Phase 7 (US5: Update)
                                                     │                                   │                           └──► Phase 8 (US6: Delete)
                                                     │                                   └──► Phase 9 (US7: History)
                                                     │
                                                     └──► (MCP tools can be built in parallel with US1 frontend)
```

### Within Each User Story

- MCP tool implementation → tool registration → verification
- Backend routes before frontend pages
- Wiring before polish

### Parallel Opportunities

**Phase 1** (all 4 tasks in parallel):
```
T001 (pyproject.toml) || T002 (package.json) || T003 (config.py) || T004 (directories)
```

**Phase 2** (3 parallel streams after T005-T007):
```
T008 (MCP server) || T009 (ChatKit Store) || T010 (Agent config)
```

**Phase 3** (backend + frontend in parallel):
```
T011-T013 (backend) || T014-T015 (frontend)  →  T016 (nav update)
```

**Phases 4+5** (can overlap since they touch the same file but different tools):
```
T017-T019 (add_task) || T020-T022 (list_tasks + summary)
```

**Phases 6+7+8** (all parallel — different tools, same file but independent functions):
```
T023-T024 (complete_task) || T025-T026 (update_task) || T027-T028 (delete_task)
```

---

## Implementation Strategy

### MVP First (User Stories 1–3)

1. Complete Phase 1: Setup (~15 min)
2. Complete Phase 2: Foundational (~2 hrs)
3. Complete Phase 3: US1 — Basic Chat (~1.5 hrs)
4. **STOP and VALIDATE**: Send "Hello" → get AI response
5. Complete Phase 4: US2 — Create Task
6. Complete Phase 5: US3 — View Tasks
7. **STOP and VALIDATE**: Create + view tasks via chat → verify in dashboard

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Basic chat working → **MVP Demo** (send message, get response)
3. US2 + US3 → Create + view tasks → **Feature Demo** (core value delivered)
4. US4 + US5 → Complete + update tasks → **Full Read-Write** (progress tracking)
5. US6 → Delete tasks → **Full CRUD** (complete capability)
6. US7 → Conversation history → **Persistence** (returning user experience)
7. Polish → Error handling, validation → **Production Ready**

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- MCP tools all go in `backend/app/mcp/tools/tasks.py` — can be added incrementally
- ChatKit Store (T009) is foundational — must work before US1 chat can persist
- Agent system instructions handle disambiguation and delete confirmation — no code needed per tool
- Verify each MCP tool with MCP Inspector before integrating with agent
- All 6 MCP tools follow the pattern in `.claude/skills/mcp-server-generator/templates/mcp-tool-template.py`

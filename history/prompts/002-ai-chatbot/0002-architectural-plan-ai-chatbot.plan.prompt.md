---
id: "0002"
title: Architectural Plan for AI Chatbot
stage: plan
date: 2026-02-10
surface: agent
model: claude-opus-4-6
feature: 002-ai-chatbot
branch: 002-ai-chatbot
user: architect
command: /sp.plan
labels: ["architecture", "mcp", "chatkit", "agents-sdk", "planning"]
links:
  spec: specs/002-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-ai-chatbot/plan.md
  - specs/002-ai-chatbot/research.md
  - specs/002-ai-chatbot/data-model.md
  - specs/002-ai-chatbot/quickstart.md
  - specs/002-ai-chatbot/contracts/api.yaml
  - specs/002-ai-chatbot/contracts/mcp-tools.yaml
  - CLAUDE.md
tests:
  - none (planning artifact, no runtime tests)
---

## Prompt

Create architectural plan for Phase 3 AI Chatbot based on specs/002-ai-chatbot/spec.md

PLAN MUST INCLUDE:
1. Database schema changes (conversations, messages tables)
2. MCP server architecture (5 tools implementation using our skill)
3. Chat API endpoint design (/api/{user_id}/chat with stateless architecture)
4. OpenAI Agents SDK integration pattern
5. Conversation state management (database persistence)
6. Frontend ChatKit integration
7. Natural language understanding flow
8. Error handling for ambiguous commands
9. Security (JWT validation, user isolation in chat context)
10. Development workflow updates

Use .claude/skills/mcp-server-generator/ skill for MCP implementation guidance.

Create plan in specs/002-ai-chatbot/plan.md

## Response snapshot

Created comprehensive architectural plan at `specs/002-ai-chatbot/plan.md` (378 lines) with 7 supporting artifacts (1,311 lines total).

**Architecture**: Three new components integrated into existing monorepo:
1. **MCP Server** (standalone, port 8001) — 6 tools (add_task, list_tasks, complete_task, update_task, delete_task, task_summary) with streamable-http transport and token passthrough auth
2. **ChatKit Backend** (integrated into FastAPI, port 8000) — ChatKitServer subclass with database-backed Store, OpenAI Agent with MCPServerStreamableHttp connection
3. **ChatKit Frontend** (new /dashboard/chat page) — @openai/chatkit-react with auth header injection

**Key decisions**: Standalone MCP server (Pattern 1), self-hosted ChatKit backend, token passthrough auth, gpt-4.1-mini model, cursor-based conversation pagination, 4-layer user isolation.

**Research decisions**: R-001 through R-006 covering ChatKit, Agents SDK, MCP architecture, Store persistence, auth flow, and agent instructions.

**Database changes**: 2 new tables (conversation, message) via Alembic migration 002.

**Contracts**: OpenAPI spec for /chatkit + /api/conversations endpoints, MCP tools contract for all 6 tools with parameters, returns, and error cases.

**Constitution check**: All 6 principles PASS. Security requirements satisfied at every layer.

## Outcome

- ✅ Impact: Complete Phase 3 architectural plan ready for task breakdown via `/sp.tasks`
- 🧪 Tests: None (planning artifact); plan specifies test strategy
- 📁 Files: 7 artifacts created + CLAUDE.md updated with Phase 3 technologies
- 🔁 Next prompts: `/sp.tasks` (generate implementation tasks), `/sp.adr` (if architectural decisions need formal recording)
- 🧠 Reflection: ChatKit SDK requires a different endpoint pattern than originally planned (/chatkit instead of /api/{user_id}/chat). The SDK handles routing internally through a single POST endpoint, which simplifies the API design but means conversation management is SDK-driven rather than custom REST.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Constitution check 6/6 PASS, all research decisions resolved
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate ChatKit Store interface matches SDK expectations during implementation

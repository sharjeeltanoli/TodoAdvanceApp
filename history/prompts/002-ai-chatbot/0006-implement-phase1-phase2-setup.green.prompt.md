---
id: "0006"
title: Implement Phase 1 and Phase 2 Setup
stage: green
date: 2026-02-11
surface: agent
model: claude-opus-4-6
feature: 002-ai-chatbot
branch: 002-ai-chatbot
user: architect
command: /sp.implement
labels: ["implementation", "setup", "foundational", "phase1", "phase2"]
links:
  spec: specs/002-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/pyproject.toml (modified — added openai-agents, openai-chatkit, mcp[cli])
  - frontend/package.json (modified — added @openai/chatkit-react)
  - backend/app/config.py (modified — added OPENAI_API_KEY, MCP_SERVER_URL, MCP_SERVER_PORT)
  - backend/.env.example (modified — added Phase 3 env vars)
  - backend/app/mcp/__init__.py (created)
  - backend/app/mcp/tools/__init__.py (created)
  - backend/app/chat/__init__.py (created)
  - backend/app/models.py (modified — added Conversation, Message SQLModel classes)
  - backend/alembic/versions/002_create_conversation_and_message_tables.py (created)
  - backend/alembic/env.py (modified — added Conversation, Message imports)
  - backend/app/mcp/server.py (created — FastMCP server scaffold with lifespan, auth, helpers)
  - backend/app/chat/store.py (created — DatabaseChatKitStore implementing Store[dict])
  - backend/app/chat/agent.py (created — Agent config with MCPServerStreamableHttp)
tests:
  - python3 import verification for all modules (PASS)
  - alembic upgrade head (PASS — migration 001→002)
  - npm install @openai/chatkit-react (PASS)
---

## Prompt

Begin Phase 3 implementation starting with Phase 1 (Setup) tasks 1-4:

1. Install OpenAI Agents SDK and ChatKit dependencies
2. Add OPENAI_API_KEY to environment configuration
3. Create backend/mcp/ directory structure
4. Create backend/chat/ directory structure

Then proceed to Phase 2 (Foundational) for database migrations and core setup.

Use .claude/skills/mcp-server-generator/ skill for MCP server implementation guidance.

## Response snapshot

Completed Phase 1 (T001-T004) and Phase 2 (T005-T010) — 10 tasks total.

**Phase 1 Setup:**
- Added openai-agents>=0.0.16, openai-chatkit>=0.0.3, mcp[cli]>=1.2.0 to pyproject.toml
- Added @openai/chatkit-react to frontend package.json
- Added OPENAI_API_KEY, MCP_SERVER_URL, MCP_SERVER_PORT to config.py and .env.example
- Created backend/app/mcp/ and backend/app/chat/ package directories

**Phase 2 Foundational:**
- Added Conversation and Message SQLModel classes to models.py
- Created Alembic migration 002 with proper indexes, FK cascades, and CHECK constraints
- Ran migration successfully against Neon PostgreSQL
- Created FastMCP server scaffold (MCP SDK v1.26.0 uses FastMCP, not MCPServer)
- Created DatabaseChatKitStore implementing all Store[dict] abstract methods
- Created Agent configuration with MCPServerStreamableHttp and system instructions

**Key discovery:** MCP SDK v1.26.0 uses `FastMCP` class (from `mcp.server.fastmcp`) instead of the older `MCPServer` (from `mcp.server.mcpserver`). The skill templates reference the older API — updated implementation to use current API.

**Key discovery:** ChatKit types use specific content types: `UserMessageTextContent(type="input_text")` for user messages and `AssistantMessageContent(type="output_text")` for assistant messages. Items require `thread_id` and `InferenceOptions` fields.

## Outcome

- ✅ Impact: Phase 1 + Phase 2 complete (10/38 tasks done, 26%)
- 🧪 Tests: Import verification for all 3 new modules passed
- 📁 Files: 13 files created/modified
- 🔁 Next prompts: Phase 3 (US1: T011-T016) — ChatKitServer, chat route, frontend chat page
- 🧠 Reflection: MCP SDK API changed significantly between template version and installed v1.26.0. Always verify SDK APIs against installed version rather than trusting templates.

## Evaluation notes (flywheel)

- Failure modes observed: MCPServer import path from template was wrong for v1.26.0; pip editable install failed (missing build_editable hook)
- Graders run and results (PASS/FAIL): All module imports PASS, migration PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Update MCP server generator skill templates to use FastMCP API

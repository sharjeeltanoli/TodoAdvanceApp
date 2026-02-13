---
id: "0004"
title: Create MCP Server Generator Skill
stage: general
date: 2026-02-10
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: architect
command: direct
labels: ["mcp", "skill", "code-generation", "phase3-prep"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/mcp-server-generator/SKILL.md
  - .claude/skills/mcp-server-generator/templates/mcp-server-template.py
  - .claude/skills/mcp-server-generator/templates/mcp-tool-template.py
  - .claude/skills/mcp-server-generator/examples/todo-mcp-example.py
tests:
  - none (skill documentation and templates, no runtime tests)
---

## Prompt

Create a reusable Claude Code skill for MCP Server generation.

SKILL PURPOSE:
Generate production-ready MCP servers using Official MCP SDK for AI agent integration.

SKILL FUNCTIONALITY:
1. Generate MCP server boilerplate (Python with Official MCP SDK)
2. Create MCP tool definitions from specifications
3. Integrate with FastAPI applications
4. Support async operations
5. Include proper error handling and validation

SKILL STRUCTURE:
Create a new skill folder: .claude/skills/mcp-server-generator/

Files needed:
- SKILL.md (main documentation and instructions)
- templates/ (code templates for MCP servers)
- examples/ (example MCP tool implementations)

SKILL.md should include:
- When to use this skill
- Input requirements (tool specifications)
- Output structure (MCP server files)
- Integration steps with FastAPI
- Best practices from Official MCP SDK

Reference the hackathon document pages 17-21 for MCP server requirements.

Make it comprehensive so we can reuse it for Phase 3 chatbot implementation.

## Response snapshot

Created a complete MCP Server Generator skill at `.claude/skills/mcp-server-generator/` with 4 files (1,242 total lines):

1. **SKILL.md** (376 lines) — Comprehensive documentation covering: when to use, prerequisites, input requirements, output structure, 3 architecture patterns (standalone, mounted, hybrid), MCP SDK core concepts (tools, resources, prompts, context, lifespan, structured output), transport options, error handling best practices, auth patterns, OpenAI Agents SDK integration, testing approaches, and a production checklist.

2. **templates/mcp-server-template.py** (143 lines) — Full server boilerplate with lifespan management (async DB + httpx), Better Auth token validation, success/error CallToolResult helpers, configurable transport/host/port, and tool registration pattern.

3. **templates/mcp-tool-template.py** (241 lines) — Reusable tool definition template with CRUD operations (list, get, create, update, delete) and a batch operation with progress tracking. All tools enforce user isolation via auth_token validation.

4. **examples/todo-mcp-example.py** (482 lines) — Complete, self-contained todo CRUD MCP server matching this project's data model. Includes 7 tools (list_tasks, get_task, create_task, update_task, toggle_task, delete_task, task_summary), 1 resource, and 1 prompt definition.

Research confirmed Official MCP Python SDK v1.2.0+ uses `MCPServer` class (formerly FastMCP), `@mcp.tool()` decorator, `Context[ServerSession, AppContext]` for typed dependencies, and supports streamable-http transport for web agent integration.

## Outcome

- ✅ Impact: Reusable skill ready for Phase 3 MCP server implementation; eliminates boilerplate creation time
- 🧪 Tests: No runtime tests (documentation/template artifact); templates include pytest example in SKILL.md
- 📁 Files: 4 files created in .claude/skills/mcp-server-generator/
- 🔁 Next prompts: Phase 3 spec creation, MCP server implementation using this skill, OpenAI Agents SDK integration
- 🧠 Reflection: Official MCP SDK has evolved — MCPServer replaces FastMCP in the SDK; standalone FastMCP project still exists separately. Both use the same decorator patterns.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review PASS — all patterns verified against official SDK README
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test templates against actual MCP Inspector once Phase 3 begins

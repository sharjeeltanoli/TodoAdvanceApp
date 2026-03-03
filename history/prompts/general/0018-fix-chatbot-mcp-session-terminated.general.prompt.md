---
id: "0018"
title: Fix chatbot not responding — MCP session terminated
stage: general
date: 2026-03-03
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: chatbot is not responding to queries. check and resolve the errors
labels: ["bugfix","mcp","chatbot","fastmcp","starlette"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/mcp_server/server.py
tests:
  - curl POST http://localhost:8000/chatkit — full streaming response received
  - curl POST http://localhost:8001/mcp — MCP initialize handshake successful
---

## Prompt

chatbot is not responding to queries. check and resolve the errors

## Response snapshot

Root cause: `mcp.shared.exceptions.McpError: Session terminated`

The MCP server (`backend/mcp_server/server.py`) used Starlette's `Mount("/mcp", app=mcp.streamable_http_app())` to embed the FastMCP sub-app into an outer Starlette app. Two problems:

1. **Lifespan not propagated**: Starlette does not propagate lifespan startup events to mounted sub-apps. The `StreamableHTTPSessionManager` task group (required by FastMCP) was never initialized, causing `RuntimeError: Task group is not initialized`.

2. **Route path mismatch**: The sub-app had `streamable_http_path="/mcp"`, but after `Mount("/mcp", ...)` strips the prefix, the sub-app received `POST /` which didn't match `/mcp`, returning 404.

**Fix**: Replaced the outer Starlette wrapper with `@mcp.custom_route()` decorators for health/dapr/events routes, then exposed `mcp.streamable_http_app()` directly as the top-level `app`. This ensures FastMCP's lifespan runs at the top level and its session manager initializes correctly.

## Outcome

- ✅ Impact: Chatbot now streams responses end-to-end; MCP tool calls (list_tasks, add_task, etc.) work
- 🧪 Tests: curl test to POST /chatkit returned full streaming SSE response from the assistant
- 📁 Files: backend/mcp_server/server.py
- 🔁 Next prompts: None identified
- 🧠 Reflection: FastMCP sub-apps must be the top-level ASGI app to receive lifespan events; mounting them inside another Starlette app silently breaks the session manager initialization

## Evaluation notes (flywheel)

- Failure modes observed: Starlette sub-app lifespan not propagating; streamable_http_path mismatch after Mount prefix stripping
- Graders run and results (PASS/FAIL): manual curl test — PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null

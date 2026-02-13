# MCP Server Generator Skill

> Generate production-ready MCP servers using the Official MCP Python SDK for AI agent integration.

## When to Use This Skill

- **Phase 3+ Implementation**: When building AI chatbot features that need MCP tool access to application data
- **New MCP Server**: When creating a standalone MCP server exposing tools, resources, or prompts
- **FastAPI Integration**: When mounting an MCP server alongside an existing FastAPI application
- **Tool Expansion**: When adding new MCP tools to an existing server
- **Agent Integration**: When connecting OpenAI Agents SDK or Claude to application functionality via MCP

## Prerequisites

```
pip install "mcp[cli]"        # Official MCP SDK (v1.2.0+)
pip install fastapi-mcp        # Optional: auto-expose FastAPI endpoints as MCP tools
```

## Input Requirements

When invoking this skill, provide:

1. **Server Name**: Descriptive name for the MCP server (e.g., `"Todo MCP Server"`)
2. **Tool Specifications**: For each tool, define:
   - Name and description
   - Input parameters with types and validation
   - Return type and structure
   - Whether it's async
   - Error cases
3. **Data Dependencies**: What databases, APIs, or services the tools need access to
4. **Transport**: `streamable-http` (recommended for web), `stdio` (for CLI), or `sse`
5. **Auth Requirements**: How the MCP server authenticates (Bearer token, API key, etc.)

## Output Structure

The generator produces:

```
backend/app/mcp/
├── __init__.py           # Package init, exports server instance
├── server.py             # MCPServer setup, lifespan, transport config
├── tools/
│   ├── __init__.py       # Tool registration
│   └── <domain>.py       # Domain-specific tool implementations
├── resources/            # (Optional) MCP resource definitions
│   └── <domain>.py
└── deps.py               # Shared dependencies (DB sessions, auth, etc.)
```

## Architecture Patterns

### Pattern 1: Standalone MCP Server (Recommended for Phase 3)

A dedicated MCP server process that connects to the same Neon database and validates tokens independently. Best when MCP clients (agents) connect over HTTP.

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("App MCP Server")

@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description for LLM context."""
    ...

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

### Pattern 2: Mounted on FastAPI (Shared Process)

Mount MCP server on the existing FastAPI app — same process, shared lifespan. Good for simple setups or when you want a single deployment.

```python
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

app = FastAPI()
# ... existing routes ...

mcp = FastApiMCP(app)
mcp.mount()  # Available at /mcp
```

### Pattern 3: Hybrid (FastAPI + Custom Tools)

Expose existing FastAPI endpoints as MCP tools automatically, plus add custom tools with richer logic.

```python
from fastapi import FastAPI
from mcp.server.mcpserver import MCPServer

app = FastAPI()
mcp = MCPServer("Hybrid Server", lifespan=app_lifespan)

# Custom tools with full control
@mcp.tool()
async def smart_search(query: str, ctx: Context) -> str:
    """AI-optimized search across all user data."""
    ...
```

## MCP SDK Core Concepts

### Tools (Function Calls)

Tools are the primary mechanism for agents to take actions. They are like POST endpoints — they execute logic and return results.

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Example")

@mcp.tool()
async def create_item(title: str, description: str = "") -> dict:
    """Create a new item. Returns the created item with its ID."""
    # Implementation here
    return {"id": "uuid", "title": title, "description": description}
```

**Key rules:**
- Docstrings become the tool description visible to the LLM — make them clear and actionable
- Parameter types are auto-extracted from type hints
- Default values make parameters optional
- Return type hints inform the LLM about response shape

### Resources (Read-Only Data)

Resources provide data to LLMs without side effects — like GET endpoints.

```python
@mcp.resource("app://user/{user_id}/profile")
async def get_user_profile(user_id: str) -> str:
    """Return user profile as JSON string."""
    ...
```

### Prompts (Reusable Templates)

Prompts define interaction patterns for agents.

```python
@mcp.prompt()
def task_summary(user_id: str) -> str:
    """Generate a summary of user's pending tasks."""
    return f"Summarize all pending tasks for user {user_id}. Group by priority."
```

### Context & Progress

Tools receive a `Context` object for logging, progress, and accessing lifespan dependencies.

```python
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.session import ServerSession

@mcp.tool()
async def long_operation(
    data: str,
    ctx: Context[ServerSession, AppContext]
) -> str:
    """Process data with progress reporting."""
    await ctx.info("Starting processing...")

    db = ctx.request_context.lifespan_context.db

    for i, chunk in enumerate(chunks):
        await ctx.report_progress(progress=i, total=len(chunks))
        await process(db, chunk)

    return "Processing complete"
```

### Lifespan Management

Use lifespan to initialize shared resources (DB pools, HTTP clients).

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

@dataclass
class AppContext:
    db: AsyncSession
    http_client: httpx.AsyncClient

@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    engine = create_async_engine(DATABASE_URL)
    async with httpx.AsyncClient() as client:
        async with AsyncSession(engine) as session:
            yield AppContext(db=session, http_client=client)

mcp = MCPServer("My Server", lifespan=app_lifespan)
```

### Structured Output

Return `CallToolResult` for full control over response format.

```python
from mcp.types import CallToolResult, TextContent

@mcp.tool()
async def validated_tool(query: str) -> CallToolResult:
    """Tool with structured output."""
    result = await do_work(query)
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(result))],
        structured_content={"status": "success", "data": result},
    )
```

## Transport Options

| Transport | Use Case | URL Pattern |
|-----------|----------|-------------|
| `streamable-http` | Web apps, agents over HTTP | `http://host:port/mcp` |
| `stdio` | CLI tools, local MCP clients | N/A (stdin/stdout) |
| `sse` | Browser clients, real-time | `http://host:port/sse` |

**Recommended for this project**: `streamable-http` — works with OpenAI Agents SDK and Claude.

```python
mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
```

Register with Claude Code:
```bash
claude mcp add --transport http todo-mcp http://localhost:8001/mcp
```

## Error Handling Best Practices

### 1. Raise descriptive errors — the LLM sees the message

```python
@mcp.tool()
async def get_task(task_id: str, ctx: Context) -> dict:
    """Get a task by ID."""
    task = await db.get(Task, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    return task.model_dump()
```

### 2. Use CallToolResult for error metadata

```python
@mcp.tool()
async def safe_operation(data: str) -> CallToolResult:
    """Operation with explicit error handling."""
    try:
        result = await process(data)
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result))]
        )
    except PermissionError:
        return CallToolResult(
            content=[TextContent(type="text", text="Permission denied")],
            isError=True,
        )
```

### 3. Validate inputs with Pydantic

```python
from pydantic import BaseModel, Field

class CreateTaskInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field("", max_length=2000)

@mcp.tool()
async def create_task(title: str, description: str = "") -> dict:
    """Create a new task."""
    validated = CreateTaskInput(title=title, description=description)
    ...
```

## Authentication Pattern for This Project

MCP tools must enforce the same user-isolation as the REST API. Two approaches:

### A. Token Passthrough (Agent provides Bearer token)

```python
@mcp.tool()
async def list_tasks(auth_token: str, ctx: Context) -> list[dict]:
    """List all tasks for the authenticated user.

    Args:
        auth_token: Bearer token from the authenticated user session.
    """
    user_id = await validate_token(auth_token, ctx)
    tasks = await fetch_tasks(user_id, ctx)
    return [t.model_dump() for t in tasks]
```

### B. Service-Level Auth (MCP server has its own credentials)

The MCP server authenticates as a service account and operates on behalf of users specified in tool parameters. Requires additional authorization checks.

## Integration with OpenAI Agents SDK

Phase 3 uses OpenAI Agents SDK with MCP servers:

```python
from agents import Agent
from agents.mcp import MCPServerStreamableHTTP

async def main():
    async with MCPServerStreamableHTTP(
        url="http://localhost:8001/mcp"
    ) as mcp:
        agent = Agent(
            name="Todo Assistant",
            instructions="Help users manage their tasks.",
            mcp_servers=[mcp],
        )
        result = await Runner.run(agent, "Show me my pending tasks")
```

## Step-by-Step: Adding a New MCP Tool

1. **Define the tool spec** (name, params, return type, description)
2. **Create/update the domain file** in `backend/app/mcp/tools/<domain>.py`
3. **Implement the tool function** with `@mcp.tool()` decorator
4. **Add error handling** (ValueError for not-found, PermissionError for auth)
5. **Test with MCP Inspector**: `mcp dev backend/app/mcp/server.py`
6. **Register with agent**: Update agent configuration to include the MCP server URL

## Testing MCP Servers

### MCP Inspector (Interactive)
```bash
mcp dev backend/app/mcp/server.py
```

### Programmatic Testing
```python
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

@pytest.mark.asyncio
async def test_list_tasks():
    async with streamablehttp_client("http://localhost:8001/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.call_tool("list_tasks", {"auth_token": TOKEN})
            assert result.content[0].text
```

## Templates Reference

| Template | Purpose |
|----------|---------|
| `templates/mcp-server-template.py` | Full server boilerplate with lifespan, auth, transport |
| `templates/mcp-tool-template.py` | Single tool definition with validation and error handling |
| `examples/todo-mcp-example.py` | Complete todo CRUD MCP server matching this project |

## Checklist for Production MCP Servers

- [ ] All tools have clear, LLM-readable docstrings
- [ ] Input validation via type hints and/or Pydantic
- [ ] User isolation enforced (every query scoped to user_id)
- [ ] Error messages are descriptive (LLM reads them)
- [ ] Lifespan manages DB connections and HTTP clients
- [ ] Progress reporting for long-running operations
- [ ] Transport configured for deployment target
- [ ] Registered with agent runtime (Claude Code or OpenAI Agents SDK)
- [ ] Tested with MCP Inspector
- [ ] No hardcoded secrets (use environment variables)

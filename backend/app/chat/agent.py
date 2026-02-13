"""
Agent Configuration
====================
Configures the OpenAI Agent with MCP server connection for task management.
The agent uses system instructions to stay focused on task management and
handles disambiguation, confirmation, and off-topic redirection.
"""

from __future__ import annotations

import os

from agents import Agent, ModelSettings, RunConfig
from agents.models.openai_provider import OpenAIProvider
from agents.mcp import MCPServerStreamableHttp

from app.config import settings

# The OpenAI Agents SDK reads OPENAI_API_KEY from os.environ directly,
# so we must propagate the value loaded by pydantic-settings.
if settings.OPENAI_API_KEY and not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# Build a RunConfig with custom provider when using a non-default base URL (e.g. OpenRouter)
_run_config: RunConfig | None = None
if settings.OPENAI_BASE_URL:
    _run_config = RunConfig(
        model_provider=OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            use_responses=False,  # OpenRouter supports Chat Completions, not Responses API
        ),
        model_settings=ModelSettings(max_tokens=1024),
        tracing_disabled=True,  # OpenRouter doesn't support OpenAI tracing
    )

# System instructions constrain the agent to task management domain
SYSTEM_INSTRUCTIONS = """\
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
"""


def create_mcp_connection(auth_token: str) -> MCPServerStreamableHttp:
    """Create an MCP server connection that passes the user's auth token."""
    return MCPServerStreamableHttp(
        params={
            "url": settings.MCP_SERVER_URL,
            "headers": {"Authorization": f"Bearer {auth_token}"},
        },
        cache_tools_list=True,
        name="todo-mcp",
    )


def get_run_config() -> RunConfig | None:
    """Return the RunConfig for the agent (None = SDK defaults)."""
    return _run_config


def create_agent(auth_token: str) -> tuple[Agent, MCPServerStreamableHttp]:
    """Create an Agent configured with MCP tools for task management.

    Returns (agent, mcp_connection) so the caller can manage the MCP lifecycle.
    """
    mcp_conn = create_mcp_connection(auth_token)

    # Inject the real auth token into system instructions so the model
    # passes it to every MCP tool call automatically.
    instructions = (
        SYSTEM_INSTRUCTIONS
        + f"\n\nIMPORTANT: For every tool call, you MUST pass the following "
        f'auth_token value exactly: "{auth_token}". '
        f"Never ask the user for their token — always use this value."
    )

    agent = Agent(
        name="Todo Assistant",
        instructions=instructions,
        model="gpt-4.1-mini",
        mcp_servers=[mcp_conn],
    )

    return agent, mcp_conn

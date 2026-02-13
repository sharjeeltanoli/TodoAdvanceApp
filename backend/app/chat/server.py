"""
ChatKit Server — Todo Assistant
=================================
Subclass of ChatKitServer that wires the OpenAI Agent to the ChatKit
streaming protocol. The respond() method loads thread history, runs the
agent, and yields ThreadStreamEvents back to the ChatKit frontend.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator

from agents import Runner
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import (
    ErrorEvent,
    ThreadItemAddedEvent,
    ThreadItemDoneEvent,
    ThreadItemRemovedEvent,
    ThreadItemUpdatedEvent,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)

from app.chat.agent import create_agent, get_run_config

logger = logging.getLogger(__name__)

# Maximum history items to load for agent context
MAX_HISTORY_ITEMS = 50

# Sentinel ID produced by the Agents SDK when using Chat Completions API
_FAKE_ID = "__fake_id__"


def _needs_real_id(item_id: str) -> bool:
    """Return True if the item ID is a placeholder that needs replacing."""
    return item_id == _FAKE_ID or not item_id


class TodoChatKitServer(ChatKitServer[dict]):
    """ChatKit server that delegates to an OpenAI Agent with MCP tools."""

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        auth_token = context.get("auth_token", "")

        # Load thread history for agent context
        history = await self.store.load_thread_items(
            thread.id,
            after=None,
            limit=MAX_HISTORY_ITEMS,
            order="asc",
            context=context,
        )

        # Convert ChatKit thread items to Agents SDK input format
        agent_input = await simple_to_agent_input(history.data)

        # Create agent with MCP connection for this request
        agent, mcp_conn = create_agent(auth_token)

        try:
            async with mcp_conn:
                # Run agent in streaming mode
                run_kwargs = {"starting_agent": agent, "input": agent_input}
                run_config = get_run_config()
                if run_config:
                    run_kwargs["run_config"] = run_config
                result = Runner.run_streamed(**run_kwargs)

                # Build AgentContext for stream_agent_response
                agent_ctx = AgentContext(
                    thread=thread,
                    store=self.store,
                    request_context=context,
                )

                # Yield ChatKit stream events, replacing placeholder IDs with
                # real UUIDs so the frontend can track each item uniquely.
                id_map: dict[str, str] = {}  # fake_id -> real_id

                async for event in stream_agent_response(agent_ctx, result):
                    yield _rewrite_ids(event, id_map)

        except Exception:
            logger.exception("Agent error during respond()")
            yield ErrorEvent(
                message="I'm having trouble right now. Please try again in a moment.",
            )


def _rewrite_ids(event: ThreadStreamEvent, id_map: dict[str, str]) -> ThreadStreamEvent:
    """Replace __fake_id__ placeholders with stable UUIDs in stream events.

    The Chat Completions adapter assigns the same ``__fake_id__`` to every
    output item.  Within a single agent turn the sequence is:
        Added(__fake_id__) → Updated(__fake_id__)* → Done(__fake_id__)
    If the agent makes a tool call and produces a second message the
    sequence repeats with the *same* ``__fake_id__``.

    We allocate a fresh UUID on each ``Added`` event and clear the mapping
    after ``Done`` so subsequent items get their own UUID.
    """

    if isinstance(event, ThreadItemAddedEvent):
        old_id = event.item.id
        if _needs_real_id(old_id):
            # Always allocate a NEW UUID when an item is first added
            new_id = str(uuid.uuid4())
            id_map[old_id] = new_id
            item = event.item.model_copy(update={"id": new_id})
            return ThreadItemAddedEvent(item=item)

    elif isinstance(event, ThreadItemDoneEvent):
        old_id = event.item.id
        if old_id in id_map:
            new_id = id_map.pop(old_id)  # pop so next Added gets a fresh UUID
            item = event.item.model_copy(update={"id": new_id})
            return ThreadItemDoneEvent(item=item)

    elif isinstance(event, ThreadItemUpdatedEvent):
        old_id = event.item_id
        if old_id in id_map:
            return ThreadItemUpdatedEvent(
                item_id=id_map[old_id],
                update=event.update,
            )

    elif isinstance(event, ThreadItemRemovedEvent):
        old_id = event.item_id
        if old_id in id_map:
            return ThreadItemRemovedEvent(item_id=id_map.pop(old_id))

    return event

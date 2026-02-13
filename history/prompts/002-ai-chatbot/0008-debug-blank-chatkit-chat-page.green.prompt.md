---
id: 0008
title: Debug Blank ChatKit Chat Page
stage: green
date: 2026-02-11
surface: agent
model: claude-opus-4-6
feature: 002-ai-chatbot
branch: 002-ai-chatbot
user: architect
command: /debug
labels: ["debugging", "chatkit", "frontend", "css", "lifecycle", "auth"]
links:
  spec: specs/002-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/chat/chat-panel.tsx
  - frontend/src/app/dashboard/chat/page.tsx
tests:
  - "Manual verification: ChatKit interface renders with input box"
  - "Manual verification: CDN script loads without error"
  - "Manual verification: Auth token passes to custom fetch"
---

## Prompt

The chat page at /dashboard/chat is rendering blank. Debug and fix the ChatKit frontend implementation.

ISSUES TO FIX:
1. Check if ChatKit component is properly initialized in components/chat/chat-panel.tsx
2. Verify ChatKit web component (<openai-chatkit>) is rendering
3. Check if custom fetch function is correctly passing auth headers
4. Ensure API endpoint configuration is correct
5. Add console logging to debug component lifecycle
6. Check if ChatKit script is loading from CDN

FILES TO INSPECT:
- frontend/components/chat/chat-panel.tsx (main ChatKit component)
- frontend/app/dashboard/chat/page.tsx (page that renders ChatPanel)
- frontend/lib/api.ts (API client with auth)

EXPECTED BEHAVIOR:
User should see ChatKit interface with input box to send messages.

Debug systematically and report findings. Add temporary console.log statements if needed.

## Response

Found 3 root causes for blank chat page:

1. **Missing `display: block` on `<openai-chatkit>` custom element** — Custom HTML elements default to `display: inline`, collapsing to zero dimensions even with `h-full w-full`. Official OpenAI ChatKit examples (openai/openai-chatkit-advanced-samples) use `className="block h-full w-full"` — ours was missing `block`.

2. **No error/ready lifecycle handlers** — Without `onReady` and `onError` event handlers on `useChatKit`, there was no way to know if ChatKit initialized or silently failed. The component rendered an empty `<openai-chatkit>` tag with no visible feedback.

3. **Silent auth failure** — If `getSession()` returned no token (e.g. expired session, not logged in), the component stayed stuck on "Loading chat..." forever with no error indication. No `.catch()` handler on the promise.

### Fixes applied

**chat-panel.tsx:**
- Added `display: block` class to `<ChatKit>` element (matches official example)
- Added `onReady` handler with loading overlay until ChatKit initializes
- Added `onError` handler with console logging for debugging
- Added auth error state with user-visible error message
- Added `.catch()` on `getSession()` to handle network failures
- Wrapped ChatKit in a `<div>` with relative positioning for overlay

**page.tsx:**
- Added `onLoad`/`onError` callbacks on the CDN Script tag for debugging

## Outcome

- **Impact:** Chat page renders correctly; 3 root causes identified and fixed
- **Files modified:** 2 (chat-panel.tsx, page.tsx)
- **Next steps:** E2E test with backend running, verify MCP tool calls work end-to-end
- **Reflection:** Custom web components defaulting to `display: inline` is a common pitfall; always check official examples for correct CSS classes

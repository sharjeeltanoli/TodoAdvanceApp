---
id: "0029"
title: Fix tag filter dropdown and tag input reset
stage: general
date: 2026-03-07
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: user
command: fix tag filter empty dropdown and tag input not clearing after create
labels: ["bug", "tags", "filter", "form-reset", "useMemo"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/tasks/task-list.tsx
  - frontend/src/components/ui/tag-input.tsx
  - frontend/src/components/tasks/task-form.tsx
tests:
  - manual: create tasks with tags, verify "All Tags" dropdown shows them
  - manual: type tag, click Add Task without pressing Enter, verify input clears
---

## Prompt

Fix two frontend UI bugs related to tags:

ISSUE 1: Tag filter dropdown empty — "All Tags" dropdown shows no actual tags.
ISSUE 2: Tag input not clearing after task creation — typed text ("lock") remains after successful create.

## Response snapshot

**Root cause — Issue 1:** `availableTags` in `task-list.tsx` was populated via `getAvailableTags()` in a `useEffect`. If that server action call failed (e.g. auth/network error), the `.catch(() => {})` silently swallowed it and `availableTags` stayed `[]`. Fixed by replacing the state + useEffect with `useMemo` that derives unique tags from the already-loaded `tasks` array — always in sync, no separate API call needed.

**Root cause — Issue 2:** `TagInput` has internal `input` state for the text field. When `task-form.tsx` resets `setPendingTag("")` and `setTags([])` after a create, the chips clear (via `value` prop) but the text input is unaffected because the internal `input` state was never told to reset. Fixed by adding an `inputValue?: string` prop to `TagInput` with a `useEffect` that syncs the internal `input` state when the prop changes. `task-form.tsx` passes `inputValue={pendingTag}`, so setting `setPendingTag("")` also clears the visible text input.

## Outcome

- ✅ Impact: Tag filter dropdown now always shows all unique tags from loaded tasks; tag text input clears correctly after task creation.
- 🧪 Tests: Manual testing required.
- 📁 Files: 3 files modified
- 🔁 Next prompts: Deploy to Vercel/Render
- 🧠 Reflection: Deriving UI state from already-fetched data (useMemo) is more reliable than a second API call. Bidirectional control for internal component state requires explicit prop+effect wiring.

## Evaluation notes (flywheel)

- Failure modes observed: Silent .catch(() => {}) hid getAvailableTags failures; TagInput internal state not accessible to parent
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment: Add error boundary or toast for failed tag fetch

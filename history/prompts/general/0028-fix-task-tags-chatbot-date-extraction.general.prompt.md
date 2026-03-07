---
id: "0028"
title: Fix task tags and chatbot date/tag extraction
stage: general
date: 2026-03-07
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: user
command: fix task creation tags and chatbot date/tag extraction
labels: ["bug", "tags", "chatbot", "function-calling", "forms"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/ui/tag-input.tsx
  - frontend/src/components/tasks/task-form.tsx
  - backend/app/routes/chat.py
tests:
  - manual: create task with tags via form — verify tags saved
  - manual: chatbot "add task go to gym on 6-mar-2026 with tag fitness" — verify date and tags saved
---

## Prompt

Fix two related issues with task creation:

ISSUE 1: Manual task creation - tags not being saved
CURRENT BEHAVIOR:
- User adds tags in task form
- Task creates successfully
- But tags are missing/empty in saved task

ISSUE 2: Chatbot task creation - missing date and tags
CURRENT BEHAVIOR:
- User: "add task go to gym on 6-mar-2026 with tag fitness"
- AI creates task with only title
- Date and tags are ignored/not extracted

## Response snapshot

**Root cause — Issue 1:** The `TagInput` component only adds a tag when Enter/comma is pressed. If the user types a tag but clicks "Add Task" without pressing Enter, the pending input is silently dropped. Fixed by adding `onInputChange` callback to `TagInput` that notifies the parent of pending input changes; `task-form.tsx` collects the pending tag in `pendingTag` state and includes it in `finalTags` on form submit.

**Root cause — Issue 2:** The `_CHAT_TOOLS` `create_task` function definition in `chat.py` was missing `due_date` and `tags` parameters, so the AI never extracted or passed them. The `_execute_tool` `create_task` handler only constructed `Task(title, description, priority)`, ignoring all other fields. Fixed by:
1. Adding `due_date` (string YYYY-MM-DD) and `tags` (array) to `create_task` and `update_task` function schemas.
2. Updating `_execute_tool` to parse the date string and pass `due_date` + `tags` to `Task()`.
3. Updating `_execute_tool` `update_task` to handle `due_date` and `tags`.
4. Updating `_SIMPLE_CHAT_SYSTEM` prompt with explicit date/tag extraction instructions.

## Outcome

- ✅ Impact: Tags typed in form are now included even if user doesn't press Enter before submitting; chatbot creates tasks with full date and tag fields.
- 🧪 Tests: Manual testing required — no automated tests added.
- 📁 Files: 3 files modified (tag-input.tsx, task-form.tsx, chat.py)
- 🔁 Next prompts: Deploy to Render/Vercel, test in production
- 🧠 Reflection: The TagInput pending-input gap is a classic controlled-component gotcha. The chat.py bug was a straightforward missing-field issue in both the tool schema and the executor.

## Evaluation notes (flywheel)

- Failure modes observed: Missing onInputChange callback caused pending tag loss; tool schema gap prevented AI from generating due_date/tags arguments
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Add integration test for tag persistence via form submit

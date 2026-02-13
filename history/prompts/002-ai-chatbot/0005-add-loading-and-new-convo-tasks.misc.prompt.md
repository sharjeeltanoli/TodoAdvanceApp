---
id: "0005"
title: Add Loading and New Conversation Tasks
stage: misc
date: 2026-02-11
surface: agent
model: claude-opus-4-6
feature: 002-ai-chatbot
branch: 002-ai-chatbot
user: architect
command: direct
labels: ["tasks", "remediation", "analysis-followup"]
links:
  spec: specs/002-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-ai-chatbot/tasks.md (modified)
tests:
  - none
---

## Prompt

Add two tasks to Phase 10 (Polish) in specs/002-ai-chatbot/tasks.md:

Task T036: Implement loading indicator in ChatPanel
- Show "Thinking..." state while agent processes
- Spinner component during streaming
- Acceptance: User sees visual feedback

Task T037: Add "New conversation" button
- Button in chat layout
- Creates new conversation in DB
- Clears chat panel
- Acceptance: User can start fresh conversation

Update task count to 38 total.

## Response snapshot

Added T036 (loading indicator, FR-019) and T037 (new conversation button, FR-011) to Phase 10 in tasks.md. Renumbered the existing T036 (quickstart update) to T038. Updated Phase 10 dependency note to reflect T032-T037 parallel, T038 sequential. Total tasks: 38. Resolves findings F1 and F2 from the /sp.analyze report.

## Outcome

- ✅ Impact: Two analysis findings (F1, F2) remediated in tasks.md
- 🧪 Tests: N/A
- 📁 Files: 1 modified (tasks.md)
- 🔁 Next prompts: /sp.implement or address remaining MEDIUM findings
- 🧠 Reflection: Straightforward task addition with renumbering

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

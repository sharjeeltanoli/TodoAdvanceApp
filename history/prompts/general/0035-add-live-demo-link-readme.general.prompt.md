---
id: "0035"
title: Add Live Demo Link README
stage: general
date: 2026-03-07
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: add live demo link to README
labels: ["documentation","readme","deployment"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - README.md
tests:
  - (no tests run)
---

## Prompt

Add live demo link to README.md file.

TASK:
Add deployment URL to README in professional format.

Live Demo URL: https://todo-advance-app.vercel.app/

ADD TO README:
Create "Live Demo" or "Deployment" section near the top with:
- Live application link
- Brief description
- Production deployment info

## Response snapshot

Added a "Live Demo" section between the badge row and the Overview section in README.md. Section includes the production URL and a one-liner describing the hosting stack (Vercel, Render, Neon).

## Outcome

- ✅ Impact: README now prominently surfaces the live deployment URL near the top
- 🧪 Tests: n/a
- 📁 Files: README.md (lines 10–16 added)
- 🔁 Next prompts: none
- 🧠 Reflection: Minimal diff — single section insert, no other content touched

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a

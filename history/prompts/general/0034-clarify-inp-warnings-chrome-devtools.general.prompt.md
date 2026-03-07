---
id: "0034"
title: Clarify INP Warnings Chrome DevTools
stage: general
date: 2026-03-07
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: clarify INP warnings
labels: ["performance","inp","chrome-devtools","next.js"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - (no files modified)
tests:
  - (no tests run)
---

## Prompt

Permanently disable INP (Interaction to Next Paint) performance warnings.

ISSUE:
Chrome DevTools showing repeated INP warnings for 200-300ms blocking times.
User wants these warnings removed completely.

FIX:
Disable performance monitoring warnings in Next.js configuration.

## Response snapshot

Investigated the codebase. `frontend/next.config.ts` already has `devIndicators: false`. No web-vitals or INP-specific JS code found in the frontend. Clarified that Chrome DevTools INP warnings are native browser UI indicators — they cannot be suppressed via Next.js config or `console.warn` overrides. Suggested either disabling the overlay in Chrome DevTools settings or fixing the root cause (long tasks from notifications/SSE).

## Outcome

- ✅ Impact: No code changes needed/possible; user informed of correct fix path
- 🧪 Tests: n/a
- 📁 Files: none modified
- 🔁 Next prompts: investigate actual INP root cause (notification/SSE handlers or heavy renders)
- 🧠 Reflection: The proposed fixes would have had no effect on native Chrome DevTools warnings; important to distinguish JS console warnings from browser-native performance overlays

## Evaluation notes (flywheel)

- Failure modes observed: User requested a code fix for a browser-native warning that cannot be suppressed via code
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): profile main thread tasks during interactions to find actual INP culprits

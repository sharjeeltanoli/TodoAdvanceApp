---
id: "0005"
title: Remediate HIGH Issues F1 through F4
stage: misc
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: 006-cloud-deployment
branch: 006-cloud-deployment
user: root
command: /sp.analyze (remediation follow-up)
labels: ["remediation","cloud-deployment","rolling-update","dapr","hpa","github-actions","security"]
links:
  spec: specs/006-cloud-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-cloud-deployment/plan.md
  - specs/006-cloud-deployment/tasks.md
tests:
  - "No tests run — artifact edits only"
---

## Prompt

Yes, apply remediation edits for all 4 HIGH issues (F1-F4):

F1: Add rolling update strategy task
- Add new task in Phase 3: Update deployment templates with maxUnavailable: 0, maxSurge: 1
- Zero-downtime rolling updates

F2: Fix Dapr tracing config
- Update dapr-configuration.yaml template in plan.md
- Remove Zipkin/Jaeger endpoint OR set samplingRate: "0"
- Keep it simple for hackathon

F3: Add MCP HPA template task
- Add task in Phase 7 (alongside T036-T039)
- Create chart/templates/hpa/mcp-hpa.yaml
- MCP server also needs auto-scaling

F4: Pin GitHub Actions versions
- Update workflow templates in plan.md
- Use SHA pins instead of tags
- Affects T016, T019, T023

Update files:
- specs/006-cloud-deployment/plan.md
- specs/006-cloud-deployment/tasks.md

Make changes pragmatic for hackathon deployment. Report all edits made.

## Response snapshot

Applied all 4 HIGH remediations across plan.md and tasks.md:

**F1 (FR-008 rolling update):**
- Added plan.md §2.5 "Rolling Update Strategy" with code example (`maxUnavailable: 0`, `maxSurge: 1`)
- Added task T050 [P] [US1] in Phase 3 (parallel with T016-T018) to update all 5 service deployment templates
- Updated critical path, parallel opportunities, task summary table, Phase 3 parallel example

**F2 (Dapr Jaeger ref):**
- Updated dapr-configuration.yaml in plan.md §1.5: removed zipkin block, set `samplingRate: "0"` with comment "Disabled — no Jaeger/Zipkin in hackathon cluster"

**F3 (MCP HPA missing):**
- Added task T051 [P] [US5] in Phase 7 to create `chart/templates/hpa/mcp-hpa.yaml` (min 1/max 2, CPU 80%)
- Added mcp-hpa.yaml to project structure in plan.md
- Updated plan.md §2.3 to include explicit HPA settings table for all 4 replicated services including MCP
- Updated T040 to verify "all 5 HPAs" (was "all 4")
- Updated task summary, parallel opportunities sections

**F4 (GitHub Actions SHA pinning):**
- Pinned all 5 Actions in plan.md workflow templates to SHA digests (10 total replacements):
  - actions/checkout → 11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
  - docker/login-action → 9780b0c442fbb1117ed29e0efdff1e18412f7567 # v3.3.0
  - docker/metadata-action → 369eb591f429131d6889c46b94e711f089e6ca96 # v5.6.1
  - docker/build-push-action → ca052bb54ab0790a636c9b5f226502c73d547a25 # v5.4.0
  - digitalocean/action-doctl → 53c3f3781a3a9b767d3dda2cf43851a638d94f3b # v2.5.1
- Updated T016, T019, T023 descriptions to reference SHA-pinned actions
- Updated T046 to use SHA-pinned gitleaks-action reference

Final task count: 49 → 51 (T050, T051 added). All 20 FRs now fully covered.

## Outcome

- ✅ Impact: All 4 HIGH sp.analyze blockers resolved; plan.md and tasks.md are consistent and ready for /sp.implement
- 🧪 Tests: No tests — artifact-level edits; verification via grep checks (0 unpinned action tags remaining, T050/T051 in all expected locations)
- 📁 Files: specs/006-cloud-deployment/plan.md, specs/006-cloud-deployment/tasks.md
- 🔁 Next prompts: /sp.implement to begin implementation
- 🧠 Reflection: Section renumbering (inserting §2.5 shifted §2.6-2.7 to §2.7-2.8) requires care — always check downstream section headers after inserting a new section in a numbered list

## Evaluation notes (flywheel)

- Failure modes observed: Section renumbering cascade after insertion — must update all shifted section headers in same edit session
- Graders run and results (PASS/FAIL): grep checks — PASS (0 unpinned tags, T050/T051 present in all 8 expected locations)
- Prompt variant (if applicable): null
- Next experiment: null

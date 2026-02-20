---
id: "0004"
title: Cross-Artifact Consistency Analysis
stage: misc
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: 006-cloud-deployment
branch: 006-cloud-deployment
user: root
command: /sp.analyze
labels: ["analysis","consistency","cloud-deployment","pre-implementation","spec-validation"]
links:
  spec: specs/006-cloud-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-cloud-deployment/spec.md
  - specs/006-cloud-deployment/plan.md
  - specs/006-cloud-deployment/tasks.md
  - specs/006-cloud-deployment/data-model.md
  - .specify/memory/constitution.md
tests:
  - "No tests run — read-only analysis"
---

## Prompt

Validate cross-artifact consistency for Phase 5C Cloud Deployment before making implementation decision.

Check:
- Spec → Plan alignment
- Plan → Tasks coverage
- All 20 FRs mapped to tasks
- Constitution compliance
- Dependencies correct
- Cloud costs reasonable
- Implementation feasible

Report any CRITICAL or HIGH issues that would block cloud deployment.

## Response snapshot

Ran full cross-artifact analysis across spec.md (20 FRs, 6 USs, 10 SCs), plan.md (7 phases), tasks.md (49 tasks T001–T049), and constitution.md.

**Result: 0 CRITICAL, 4 HIGH, 5 MEDIUM, 3 LOW issues. 100% FR coverage (14 full, 3 partial/assumed).**

HIGH issues found:
- F1: FR-008 partial — no task sets maxUnavailable: 0 in deployment templates (rolling update strategy missing)
- F2: dapr-configuration.yaml references Jaeger/Zipkin endpoint never installed (causes Dapr tracing errors)
- F3: MCP HPA template task missing — mcp-hpa.yaml never created despite values-production.yaml + plan §2.3 requiring it
- F4: Constitution violation — GitHub Actions use mutable version tags (@v4, @v5) not pinned SHAs

Cost: $88.50/mo verified accurate. ~2.3 month runway on $200 credit.

Recommended: Resolve F1–F4 before /sp.implement.

## Outcome

- ✅ Impact: Full cross-artifact consistency map produced for 006-cloud-deployment; 4 HIGH blockers identified before implementation
- 🧪 Tests: Read-only analysis — no tests run
- 📁 Files: Read-only — spec.md, plan.md, tasks.md, data-model.md, constitution.md analyzed
- 🔁 Next prompts: Remediate F1–F4 in plan.md/tasks.md, then /sp.implement
- 🧠 Reflection: Jaeger reference (F2) is a subtle infrastructure inconsistency — dapr-configuration references a service from a different stack (Jaeger/Zipkin) that was never planned for installation. Always cross-check external service references in config templates against the actual install tasks.

## Evaluation notes (flywheel)

- Failure modes observed: F2 (Jaeger ref) is easy to miss — plan reused a Dapr tracing template without verifying monitoring stack compatibility
- Graders run and results (PASS/FAIL): Manual cross-reference — PASS for coverage analysis, FAIL for F1–F4
- Prompt variant (if applicable): null
- Next experiment: Add Jaeger/Zipkin compatibility check to sp.analyze detection passes for infrastructure projects

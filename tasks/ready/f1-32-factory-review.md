---
id: f1-32-factory-review
milestone: f1
depends_on: [f1-27-bench, f1-28-bench-page, f1-29-project-page, f1-38-project-page-fixes]
agent: lead
difficulty: 7
commands: [uv run runner report, uv run runner backfill, uv run runner run --dry-run]
files:
  - docs/reviews/factory-f1.md
  - docs/agents/lead.md
tests:
  - tests/runner/test_report.py
---

### Goal
Review the whole factory flow with the evidence f1 now holds, and write what to change.

### Context
Read `docs/agents/lead.md`, `docs/workflow.md`, `docs/adr/02-software-factory.md` (its learnings log), `docs/milestones/f1.md` (its Replan log above all), the f0 rehearsal's fixes (`git show b73e4c0 78470aa`), and `docs/sessions/` since `f1-start`. Numbers come from `uv run runner report f1` and the dashboard's queries, not from reading logs.
- **What to look at:** the runner (loop, gates, caps, restarts), the prompts, the ticket format and craft, the docs every agent reads, and the owner's touchpoints (plan, "go", the verdict, sign-off). For each: what the evidence says, and what it cost.
- **Measure the replans** (f1-07, f1-19): what each changed, whether a later ticket needed it, and what it cost. Recommend whether replans become standard, and how often (after lead-ticket chains, or at checkpoints on the lead model).
- **Output:** `docs/reviews/factory-f1.md` with findings graded blocking / should-fix / nit, each routed: a fix you make now (keeping `check-all` green), a ticket for a later milestone (in the report, not in `tasks/ready/`), or a draft ADR (Proposed) for what the owner decides.
- **Facts from the 2026-10-01 mid-milestone review** (the metrics database; check them against `uv run runner report f1`):
  - D7's seed rate ($7.9 per 1,000 lines, from M4) is 2.7× f1's measured lead rate (f1-04 to f1-06: $9.13 for 3,155 lines, $2.9 per 1,000). "Supporting" leaves out the interactive planning and the f0 rehearsal sessions.
  - Of the $10 of headless support for 17 developer tickets, $8.06 went to the 6 that failed; a first-time pass cost about $0.17 (its checkpoint share). f1-34 cost $2.40 for 57 lines.
  - Lead tickets were 65% of headless Claude ($18.7 of $28.7). Checkpoints on Sonnet: $0.24 each, 4 real bugs.
  - f1-07 (the first replan) cost $3.94, changed no Decision, and found the gates' blind spot (f1-33).
  - ADR 15 changed the flow mid-milestone. Measure parking, the reserve question, build-on and `finish` from their jobs, if f1 used them.
- **From now on,** every milestone review has a standing "Factory" section: add it to "Review" in `docs/agents/lead.md`.

### Done when
- `docs/reviews/factory-f1.md` exists with findings, routes and the replan verdict, each backed by a number or a file
- lead.md's "Review" asks for a "Factory" section
- `uv run runner check-all --task f1-32-factory-review` passes

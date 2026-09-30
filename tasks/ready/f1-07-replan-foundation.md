---
id: f1-07-replan-foundation
milestone: f1
depends_on: [f1-06-dashboard-service]
agent: lead
difficulty: 5
commands: [uv run runner run --dry-run, uv run runner report]
files:
  - docs/milestones/f1.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
Check the rest of f1's plan against what f1-01 to f1-06 actually built, and fix the plan before developers and later lead tickets build on it.

### Context
A replan: midway reviews of the plan, tried for the first time in f1. Read `docs/milestones/f1.md`, the merged code (`git log f1-start..`, `git show`), the session reports in `docs/sessions/` since `f1-start`, and `uv run runner report f1` for the jobs so far. Check most closely what the developer page tickets rely on: `runner/metrics.py`'s columns, `factory_dashboard/queries.py`'s functions, and the worked example (`factory_dashboard/overview.py`, its template and test, and the entry in `docs/agents/junior.md`).
- **Decisions:** where the code differs from `docs/milestones/f1.md`, update the Decisions to match the code, unless the code is wrong; then write a fix ticket.
- **Tickets in `tasks/ready/`** that now name a wrong file, function, column, flag or fact: edit them, adding facts, not solutions (`docs/task-writing.md`). Split one that has grown past about two of your steps. A new ticket takes the next free number (f1-33 on), and the tickets that need it list it in `depends_on`.
- **Scope stays as agreed:** no new pages or features. Nice-to-haves go to `docs/roadmap.md`.
- **What the owner decides** (`docs/agents/lead.md`, "The owner"): draft an ADR (Proposed), and move the tickets it affects to `tasks/blocked/` with one line on why, so they and their dependants wait for the owner.
- **Always** add a dated entry to "Replan log" at the end of `docs/milestones/f1.md`: what you checked, what you changed and why, or "no change". Five lines at most.

### Done when
- every ticket in `tasks/ready/` names only files, functions and columns that exist or that an earlier ticket creates (`uv run runner run --dry-run` shows no other pre-flight problem)
- `docs/milestones/f1.md` has a Replan log entry for this ticket
- `uv run runner check-all --task f1-07-replan-foundation` passes

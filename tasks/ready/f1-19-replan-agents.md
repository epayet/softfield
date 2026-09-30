---
id: f1-19-replan-agents
milestone: f1
depends_on: [f1-18-probes]
agent: lead
difficulty: 5
commands: [uv run runner run --dry-run, uv run runner report]
files:
  - docs/milestones/f1.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
Check f1's agent tickets (f1-20 on) against what the probes found, and fix the plan before the adapters, ratings and router are built.

### Context
A replan (the second in f1; the first was f1-07). Read the probe facts in `docs/adr/14-developers-and-agents.md` and the fixtures f1-18 saved, `docs/milestones/f1.md` (including its Replan log), the merged code since `f1-start`, and `uv run runner report f1`. Check most closely: Copilot's real flags, models and requests per prompt against f1-22 and f1-26; Ollama's model tags and refusal shape against f1-21 and f1-25; whether any billing or usage reading exists, against f1-25 and f1-30 (the forecast learns from past refusals when no API answers). A probe that couldn't run (a missing login) means its tickets wait: move them to `tasks/blocked/` with the login the owner owes.
- **Decisions:** where the code differs from `docs/milestones/f1.md`, update the Decisions to match the code, unless the code is wrong; then write a fix ticket.
- **Tickets in `tasks/ready/`** that now name a wrong file, function, column, flag or fact: edit them, adding facts, not solutions (`docs/task-writing.md`). Split one that has grown past about two of your steps. A new ticket takes the next free number (f1-33 on), and the tickets that need it list it in `depends_on`.
- **Scope stays as agreed:** no new pages or features. Nice-to-haves go to `docs/roadmap.md`.
- **What the owner decides** (`docs/agents/lead.md`, "The owner"): draft an ADR (Proposed), and move the tickets it affects to `tasks/blocked/` with one line on why, so they and their dependants wait for the owner.
- **Facts from f1-07:** `test_queued_tickets_name_only_what_exists_or_an_earlier_ticket_creates` in `tests/runner/test_tasks.py` runs every queued ticket's pre-flight, allowing a path that a ticket it depends on creates; the dry run shows the same problems. `uv run runner report f1` writes its numbers into `docs/reviews/f1.md` (a snapshot the review refreshes). The job key is (run, ticket, role, attempt): the agent isn't in it (f1-25, f1-27).
- **Always** add a dated entry to "Replan log" at the end of `docs/milestones/f1.md`: what you checked, what you changed and why, or "no change". Five lines at most.

### Done when
- every ticket in `tasks/ready/` names only flags, tags, files and functions the probes and the code confirm (`uv run runner run --dry-run` shows no other pre-flight problem)
- `docs/milestones/f1.md` has a Replan log entry for this ticket
- `uv run runner check-all --task f1-19-replan-agents` passes

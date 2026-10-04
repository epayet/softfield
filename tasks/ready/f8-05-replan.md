---
id: f8-05-replan
milestone: f8-one-queue
depends_on: [f8-03-support-jobs-queued, f8-04-reserve-switches]
agent: lead
difficulty: 3
files:
  - docs/milestones/f8-one-queue.md
  - tasks/ready/f8-06-switch-buttons.md
  - tasks/ready/f8-07-queue-view.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
F8's remaining tickets, f5-18 (pause) and F6's planner tickets match what f8-01 to f8-04 built.

### Context
Read `docs/agents/lead.md` ("Replans"), D1–D4 in `docs/milestones/f8-one-queue.md`, the code f8-01…04 merged (`git log`), and the ready tickets `tasks/ready/f8-06-switch-buttons.md`, `tasks/ready/f8-07-queue-view.md`, `tasks/ready/f5-18-pause.md`, `tasks/ready/f6-01-planner-threads.md`.
- f5-18's pause becomes a state of `pick` (ADR 22 item 5); f6-01's "planner jobs first" becomes the `planner` kind in `pick` and a queued row per message.
- Fix each ticket's Context to name the functions as built. Log what you changed under "## Replan" in `docs/milestones/f8-one-queue.md`.

### Done when
- every fact in those four tickets matches the code, and `uv run pytest -q tests/runner/test_tasks.py` passes
- the replan log lists each change

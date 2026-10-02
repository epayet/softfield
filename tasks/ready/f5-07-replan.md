---
id: f5-07-replan
milestone: f5-board
depends_on: [f5-02-requests-route, f5-06-priority-pick]
agent: lead
difficulty: 3
files:
  - docs/milestones/f5-board.md
  - tasks/ready/f5-08-signoff-button.md
  - tasks/ready/f5-09-queue-button.md
  - tasks/ready/f5-10-five-hour-buttons.md
  - tasks/ready/f5-11-queue-priority.md
  - tasks/ready/f5-15-board-data.md
  - tasks/ready/f5-16-board-page.md
  - tasks/ready/f5-17-card-page.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
F5's Decisions and its developer tickets match what f5-01 to f5-06 built, before developers rely on them.

### Context
Read `docs/milestones/f5-board.md` (Decisions D1–D6), the diffs of f5-01 to f5-06 (`git log --oneline`, `git show`) and tickets f5-08 to f5-11 and f5-15 to f5-17 in `tasks/ready/`. ADR 16 item 7.
- Check every name, route, field and fact the tickets give against the code: function names, the partial's path, the request kinds, how a milestone page knows all its tickets are done, and how the 5-hour Needs-you item is recognised (`owner_items.kind = 'five-hour'`).
- Fix what's wrong in the tickets and the Decisions; add facts, not solutions. Log what you changed in a "Replan" section at the end of the milestone doc.

### Done when
- every backticked path and named function in tickets f5-08 to f5-11 and f5-15 to f5-17 exists
- `uv run pytest -q tests/runner/test_tasks.py` passes
- the milestone doc has its Replan section

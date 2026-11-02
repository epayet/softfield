---
id: f6-19-replan
milestone: f6-planning-room
depends_on: [f6-13-replan-edits-ready, f6-16-top-bar-status, f6-18-priority-buttons]
agent: lead
difficulty: 3
files:
  - docs/milestones/f6-planning-room.md
  - docs/agents/lead.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
F6's Decisions match what f6-13 to f6-21 built, and the owner's steering loop (pause, talk on a card, approve a replan or reorder, resume) works end to end from the dashboard, or what's missing is a ticket.

### Context
Read F6's D1, D2, D4 and D6 in `docs/milestones/f6-planning-room.md`, its ticket table and "Later", and the merges of f6-13, f6-14, f6-15, f6-16, f6-17, f6-18, f6-20 and f6-21 (`git log --oneline -- runner/ factory_dashboard/`).
- The owner (2026-10-07), the aim: "the next step is still to steer, plan and chat through the ui", so the owner stops the runner for a terminal chat less often.
- Walk the loop against the code: a pause, a message on a card while paused (f6-14), the lead's `replan` proposal editing a ready ticket (f6-13), approval lifting the pause, a priority change (f6-18), a seed removed (f6-17); and what the owner sees at each step (f6-15, f6-16, f6-20, f6-21). For each gap, write a ticket in `tasks/ready/` (developer when it is small and follows an example; lead otherwise) or a "Later" line.
- Record the replan in a "Replan" entry, as f6-05's, and keep lead.md's "Planning room" section pointing at what changed.

### Done when
- F6's doc says what was built, as built, and lists every gap found as a ticket or a "Later" line
- `uv run pytest -q tests/runner/test_tasks.py` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

---
id: f191-02-escalated-ticket-keeps-the-lane
milestone: f191-why-is-the-lead-reviewing-something
agent: lead
difficulty: 4
depends_on: [f191-01-lane-before-every-project-s-queue]
files:
  - runner/loop.py
  - tests/runner/test_loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
The escalation of a fast-lane ticket keeps the lane's place, though the escalation moved its ticket from `.softfield/tasks/ready/` to `.softfield/tasks/escalated/`.

### Context
Read "What happened" (cause 2) and D2 in `.softfield/cards/f191-why-is-the-lead-reviewing-something.md`.
In `runner/loop.py`: `reserve_cards` (reads the ready tickets only), `work_queue` (passes it as `first` to `dispatch.pick`), `dry_run_plan` (passes it to `dispatch.plan`) and the round's lane pass from `f191-01-lane-before-every-project-s-queue`. `load_dir` reads a tickets folder; `s.tasks_dir("escalated")` is the folder.
`reserve_cards` keeps its meaning (the tickets that may use the reserve, `_uses_reserve`); the escalated lane tickets join `first` beside it.
On 2026-10-29, 20:12 to 20:30, four planner jobs ran before the escalations of two tickets of F172 and F146, both cards in the fast lane.

### Done when
- A queued escalation (or direction) of a ticket in `.softfield/tasks/escalated/` whose card is in the fast lane runs before a planner job, a checkpoint and a review, in `work_queue` and in the round's lane pass.
- The same escalation of a card not in the lane keeps today's place.
- `softfield run --dry-run` lists it in the lane, as the run takes it.
- `reserve_cards` returns what it does today (`test_reserve_cards_follows_the_ready_tickets_only` passes unchanged).

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

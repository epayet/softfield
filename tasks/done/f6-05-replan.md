---
id: f6-05-replan
milestone: f6-planning-room
depends_on: [f6-03-proposals-approval, f6-04-plant-ideas]
agent: lead
difficulty: 3
files:
  - docs/milestones/f6-planning-room.md
  - tasks/ready/f6-06-desk-page.md
  - tasks/ready/f6-07-thread-page.md
  - tasks/ready/f6-08-proposal-review.md
  - tasks/ready/f6-09-needs-you-desk.md
  - tasks/ready/f6-10-planning-phone.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
F6's Decisions and its developer tickets match what f6-01 to f6-04 built, before developers rely on them.

### Context
Read `docs/milestones/f6-planning-room.md`, the diffs of f6-01 to f6-04 (`git log`, `git show`) and tickets f6-06 to f6-10. ADR 16 item 7.
- Check every table, request kind, field, function and route the tickets name against the code. Fix the tickets and Decisions (facts, not solutions), and log it in a "Replan" section of the milestone doc.

### Done when
- every backticked path and named function in f6-06 to f6-10 exists
- `uv run pytest -q tests/runner/test_tasks.py` passes
- the milestone doc has its Replan section

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

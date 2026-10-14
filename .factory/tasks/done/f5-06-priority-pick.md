---
id: f5-06-priority-pick
milestone: f5-board
depends_on: [f5-04-cards, f5-05-bug-tickets]
agent: lead
difficulty: 4
files:
  - runner/tasks.py
  - runner/loop.py
tests:
  - tests/runner/test_tasks.py
---

### Goal
The runner picks the next ticket by priority first, then milestone order, then id, so reordering cards changes what runs next.

### Context
Read `docs/adr/19-feature-board.md` item 3, D6 in `docs/milestones/f5-board.md`, `runner/tasks.py` (`pick_next`) and the priorities f5-04 (cards) and f5-05 (tickets) added. Test-first.
- A ticket's priority is its own `priority:`, else its milestone card's, else 100. Lower goes first. Dependencies, pauses and the `After:` rule (f4-15) still apply before the order.
- `runner run --dry-run` prints each ticket's priority.

### Done when
- of two runnable tickets, the one in a priority-1 milestone goes before one in an earlier milestone with priority 5
- a bug with `priority: 1` goes before milestone tickets with priority 2
- equal priorities keep today's order
- `uv run runner check-all --task f5-06-priority-pick` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

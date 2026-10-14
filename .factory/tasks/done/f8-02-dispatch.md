---
id: f8-02-dispatch
milestone: f8-one-queue
depends_on: [f8-01-work-queue-table]
agent: lead
difficulty: 6
files:
  - runner/dispatch.py
  - runner/loop.py
tests:
  - tests/runner/test_dispatch.py
---

### Goal
One pure function says which job runs next and why, from the queued jobs, the ready tickets, Claude's windows and the time.

### Context
Read `docs/adr/22-one-visible-queue.md` (items 2 and 6), D2 in `docs/milestones/f8-one-queue.md`, and where the order lives today in `runner/loop.py`: `work_queue`, `_resume_support`, `lead_work_ready`, `_next_task`, `at_five_hour`, `_due_review`, and `pick_next` in `runner/tasks.py`. Test-first.
- **Same order as today, first** (ADR 22, Risk): before anything else, tests pin today's choices (a parked escalation past its reset before a ticket; a due review before the next ticket; lead work before a developer ticket for Claude) and `pick` must make them.
- `uv run runner run --dry-run` prints `pick`'s list, each line with its reason. The loop doesn't call `pick` yet: f8-03 does.

### Done when
- a test per rule above, and one with every kind queued that returns them in D2's order
- a queued row with `not_before` in the future is skipped, and the dry run says until when
- `uv run runner check-all --task f8-02-dispatch` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

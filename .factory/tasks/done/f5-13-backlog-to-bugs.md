---
id: f5-13-backlog-to-bugs
milestone: f5-board
depends_on: [f5-05-bug-tickets]
agent: lead
difficulty: 3
files:
  - docs/backlog.md
  - .factory/cards/bugs.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
Every item in `docs/backlog.md` is triaged into a bug ticket in `.factory/tasks/later/` with a priority, or dropped with a reason, and the backlog file points at the bug tickets.

### Context
Read `docs/backlog.md`, `.factory/cards/bugs.md` and `docs/task-format.md` (bug tickets, `priority:`). `docs/task-writing.md` covers how to write each one.
- Write one ticket per item still worth doing, `bug-<nn>-<slug>` with `milestone: bugs`, a priority (lower first; the factory before the product for now, owner 2026-10-02) and a difficulty. Put them in `.factory/tasks/later/`: the owner queues the ones they want.
- Items that are lead work (protected paths) get `agent: lead`. Items that are decisions, not fixes (the product name), stay in the backlog as notes.

### Done when
- every backlog bullet is a ticket in `.factory/tasks/later/`, or stays with a one-line reason
- `uv run pytest -q tests/runner/test_tasks.py` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

---
id: f5-05-bug-tickets
milestone: f5-board
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/tasks.py
  - runner/loop.py
  - runner/review.py
  - docs/task-format.md
  - docs/milestones/bugs.md
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_loop.py
---

### Goal
Bugs are tickets outside milestones: `bug-<nn>-<slug>`, `milestone: bugs`, with an optional priority, done when they merge and never signed off or reviewed.

### Context
Read `docs/adr/19-feature-board.md` item 2, D5 in `docs/milestones/f5-board.md`, `runner/tasks.py` (how ids and `milestone:` are parsed and checked), `runner/loop.py` (`work_queue`, checkpoints) and `runner/review.py`. Test-first.
- `bugs` is a standing milestone key. The milestone commands refuse it (`runner milestone bugs`, `review`, `signoff`), but `runner run` takes its tickets. Checkpoints count their merges like any developer merge.
- Frontmatter gains `priority:` (an integer), optional for any ticket, default 50 for a bug.
- Write `docs/milestones/bugs.md` (a short page: what a bug ticket is, `**State:** building`). Document the id, the key and `priority:` in `docs/task-format.md`.

### Done when
- a `bug-01-x` ticket with `milestone: bugs` passes pre-flight and runs under `runner run`
- `runner signoff bugs` and `runner milestone bugs` refuse with a clear message
- a ticket with `priority: 3` is parsed; a missing one defaults as above
- `uv run runner check-all --task f5-05-bug-tickets` passes

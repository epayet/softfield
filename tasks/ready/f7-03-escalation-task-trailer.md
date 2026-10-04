---
id: f7-03-escalation-task-trailer
milestone: f7-factory-fixes
depends_on: []
agent: lead
difficulty: 2
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
An escalation that implements a ticket commits with the ticket's `Task:` trailer, so every merged ticket's commit can be found by it.

### Context
Read `handle_escalation` and `_finish_branch` in `runner/loop.py` (the commits "escalation <id>: <outcome> (by Claude)"), `with_trailers` in `runner/gitops.py`, and "Who made each commit" in `docs/workflow.md`. Test-first.
- f4-24's escalation implemented it with only `Agent: claude-headless` (commit `05fca79`), so `runner bench --review f4-always-on` stopped on "no merge of f4-24…" until the bench learned to fall back to `tickets.commit` (`merge_commit` in `runner/bench.py`).
- Only the `implemented` outcome merges the ticket; the others don't take the trailer.

### Done when
- an escalation whose outcome is `implemented` commits with `Task: <id>` and `Agent: claude-headless`; a repaired or requeued one has no `Task:`
- `uv run runner check-all --task f7-03-escalation-task-trailer` passes

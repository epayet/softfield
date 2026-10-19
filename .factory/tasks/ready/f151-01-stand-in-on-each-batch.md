---
id: f151-01-stand-in-on-each-batch
milestone: f151-i-had-to-restart-the-runner
depends_on: []
agent: lead
difficulty: 1
priority: 1
area: factory
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
While Claude is held, each batch of `checkpoint_every` developer merges gets its stand-in checkpoint at the next pick, even when an earlier stand-in left the checkpoint row parked for Claude's re-check; the owner no longer has to restart the runner to get it.

### Context
Read "What happened" and Decisions D1–D2 in `.factory/cards/f151-i-had-to-restart-the-runner.md`. In `runner/loop.py`: `note_merge` (the `find_row(s, CHECKPOINT) is not None` early return), `_row_waits`, `_unpark_row`, `checkpoint` and `stand_in_checkpoint` (don't change these two), `_park_support`. In `tests/runner/test_loop.py`: `test_two_stand_in_checkpoints_then_claude_free_make_one_claude_recheck_of_all_their_merges` (its helpers `_claude_at`, `_fake_copilot`, `COPILOT`, `ROLES`) and `test_a_parked_checkpoint_survives_a_restart_as_a_row_and_runs_after_its_reset`.
- On 2026-10-17 the runner idled from 11:55 to the owner's restart at 13:00 with five unchecked merges and the checkpoint parked until Monday 17:00.

### Done when
- a developer merge that brings `state.unchecked` to `checkpoint_every` or more while the checkpoint row is parked until a later time makes that row due at the next pick; through `work_queue`, with Claude held and a stand-in configured, the stand-in reviews only the new unchecked merges and the row parks again with all of them for Claude's re-check
- with fewer unchecked merges than `checkpoint_every`, or a checkpoint row that isn't parked, `note_merge` does as today
- a stand-in that may not run (none configured, or past its cap) leaves the row parked again and the developer tickets go on, as today
- the listed `tests:` pass, and the new test fails without the change
- all gates pass (see `docs/workflow.md`)

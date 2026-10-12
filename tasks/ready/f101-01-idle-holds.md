---
id: f101-01-idle-holds
milestone: f101-uv-runner-run-command-stopped-when
difficulty: 6
depends_on: []
agent: lead
files:
  - runner/loop.py
  - runner/cli.py
  - docs/workflow.md
tests:
  - tests/runner/test_loop.py
---

### Goal
`uv run runner run` holds when it has nothing to run, saying what it waits for and applying the owner's requests, and picks again by itself; it no longer ends.

### Context
Read `docs/milestones/f101-uv-runner-run-command-stopped-when.md` (D1 to D3), then `work_queue`, `_wait_for_reset`, `_hold_for_the_owner`, `apply_owner_requests`, `set_activity` and `close_session` in `runner/loop.py`, and how `runner/cli.py` calls `run_session`. `runner/**` is protected: write the tests first, each failing for the right reason.
- The hold is `_hold_for_the_owner`'s loop with another reason: every `HOLD_POLL_S` it applies requests, checks the backup, takes a fresh reading, and ends as soon as the pick would return a job.
- Only under `reviews=True` without `once` (the standing `runner run`). `runner milestone`, `--once` and `--dry-run` end as today.
- The idle line names each cause once: tickets parked for Claude with the earliest reset, tickets paused behind a blocked or escalated one, and the open owner items by kind. It is logged when it changes, not at every poll.
- A due review still ends the queue for the command to run it, as today.
- **The hold never spends Claude: no job starts from it but through the normal pick.**

### Done when
- every ready ticket parked at the weekly reserve, switch off: `work_queue` doesn't return; the activity says how many wait and when the week resets
- the reserve switch turned on by a request during the hold: the next pick runs a ticket
- an empty `tasks/ready/`: the hold says nothing is ready; a ticket appearing there (an approved plan) is picked
- the idle line is logged once while nothing changes, and again when its causes change
- `once=True`, and `runner milestone`'s queue, return as before
- `docs/workflow.md` says the standing command stays up and how to end it
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f4-20-run-reviews-milestones
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/loop.py
  - runner/milestone.py
  - runner/cli.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_milestone.py
---

### Goal
Under `runner run`, a milestone whose tickets are all done gets its review and its verdict, as `runner milestone` gives it, and the run then carries on with the other milestones' tickets.

### Context
Read `docs/adr/17-always-on-factory.md` (item 4: `runner run` is the standing command), `runner/milestone.py` (`run_milestone`: the review loop, the verdict, the `-start` tag), `runner/loop.py` (`work_queue`, `run_session`) and `runner/cli.py` (both commands, `_restart`). Test-first.
- **Why:** since 2026-10-03 the owner leaves `runner run` on, and it never starts a review. Only `runner milestone <key>` does, after its own tickets. F4 would finish with no review, no sign-off sheet and no Needs-you item.
- **When `runner run` has nothing left to pick for a milestone**, start that milestone's review loop:
  - every ticket of that milestone is in `done/`;
  - it isn't `bugs`;
  - it isn't signed off;
  - it has no review yet.

  Run it as `run_milestone` does after its queue (same caps, same stop rules), record its verdict, then go back to the queue. One review at a time.
- **Restarts:** a review that changes runner/ restarts the command like a ticket does. The review's state lives in the runner's state file (`review_counts` in `var/runs/state.json`), so the restarted run carries on with it.
- `runner milestone <key>` keeps working as it is.

### Done when
- a fake run where F9's last ticket merges while F10 still has tickets reviews F9, records its verdict, and then runs F10's next ticket
- a milestone already reviewed, or signed off, isn't reviewed again
- `uv run runner check-all --task f4-20-run-reviews-milestones` passes

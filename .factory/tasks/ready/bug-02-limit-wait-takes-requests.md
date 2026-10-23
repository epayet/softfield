---
id: bug-02-limit-wait-takes-requests
milestone: bugs
difficulty: 6
depends_on: []
agent: lead
area: factory
priority: 11
finding: f101-uv-runner-run-command-stopped-when-F3
files:
  - runner/loop.py
  - docs/workflow.md
tests:
  - tests/runner/test_loop.py
---

### Goal
While `softfield run` waits for a Claude limit to reset with nothing else to run, it applies the owner's requests as they come and starts whatever they make runnable, as the idle hold does since F101.

### Context
Read `def _wait_for_reset`, `def wait_for_claude`, `def _idle_holds`, `def _idle_line`, `def _hold_for_the_owner` and `def work_queue` in `runner/loop.py`, and in `tests/runner/test_loop.py` `test_waiting_with_nothing_to_run_without_claude_shows_on_the_run` and `test_the_reserve_switch_turned_on_while_the_run_is_idle_runs_the_tickets` (the worked example, with `def _idles`). `runner/**` is protected: write the tests first, each failing for the right reason.
- Today: a lead ticket parked for a limit Claude refused (not the reserve) with no developer ticket runnable makes `_wait_for_reset` sleep to the reset in one `time.sleep`, up to 5 hours or the rest of the week. Only the 5-hour switch is read meanwhile, and only for work held by the owner's share. A plant, a message, an approved plan, a pause, a queued ticket all wait for the reset: the standing runner is up and deaf, which F101 set out to end ("applies every request from the dashboard as it comes").
- The run is git's one writer and nothing else runs during the wait, so it may apply every request there (`apply_owner_requests`), as the pause's hold and the idle hold do, every `HOLD_POLL_S`.
- The wait ends early when a request made something runnable: a developer ticket queued or approved, a planner job (they run under the reserve), a switch. With nothing new it goes on to the reset.
- Kept as they are: the one `wait` usage event per wait (from its start to the reset; an early end and a new wait for the same reset add no second event, or the clogged hours count twice), the activity "waiting for Claude · <what> until HH:MM" with its `waiting_until`, `paused_until` in the state, the backup check, and the one console line per wait.
- `runner milestone` and `--once` may keep the plain sleep if that is simpler; say which in `docs/workflow.md`, one sentence beside F101's paragraph.
- `_idle_line`'s "for Claude until …" branch can't be reached today (`_wait_for_reset` takes every such ticket first). Use it or remove it, and test what stays.

### Done when
- a lead ticket parked for a limit two hours ahead, nothing else runnable: a developer ticket that reaches the ready folder during the wait (an approved plan) runs within one poll, and the lead ticket still runs after the reset
- a plant made during the wait gets its planner job before the reset
- a pause asked during the wait is taken: the run holds "paused by you", and a resume brings the wait back
- with no request, the run sleeps to the reset as now: the same activity and `waiting_until`, and exactly one `wait` usage event, whatever came in meanwhile
- Ctrl-C during the wait ends the run as it does today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

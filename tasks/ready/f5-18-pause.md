---
id: f5-18-pause
milestone: f5-board
depends_on: [f5-01-requests-apply, f5-02-requests-route, f8-03-support-jobs-queued, f8-04-reserve-switches]
agent: lead
priority: 1
difficulty: 5
files:
  - runner/requests.py
  - runner/dispatch.py
  - runner/state.py
  - runner/loop.py
  - runner/cli.py
  - factory_dashboard/requests.py
  - factory_dashboard/queries.py
  - factory_dashboard/templates/_partials/running.html
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_dispatch.py
  - tests/runner/test_loop.py
  - tests/runner/test_cli.py
  - tests/factory_dashboard/test_requests.py
---

### Goal
From the Overview, the owner can pause the factory: the runner finishes the job it is on, then holds until the owner resumes. They can then talk to the lead about what they saw, without the line moving on meanwhile.

### Context
Read `docs/milestones/f5-board.md` (D1–D3), item 5 of `docs/adr/22-one-visible-queue.md`, `runner/requests.py` (`apply_requests`, `take_switches`), `runner/dispatch.py` (`pick`, `plan`), `work_queue` and `wait_for_claude` in `runner/loop.py`, `factory_dashboard/requests.py` (`POST /requests`, its guard and `KINDS`), and `factory_dashboard/templates/_partials/running.html` (Now). Test-first.
- **Why (owner, 2026-10-03):** "It would be good to be able to direct a milestone as it's happening if I notice something, trigger a replan from the result of the chat. Might be worth pausing while I chat about it." The chat and the replan are F6's (the planning room); this is the pause.
- **Two request kinds** in D1's table: `pause` and `resume`, with no subject and no value.
  - `apply_requests` records the pause, with its time, in a new `State` field (`runner/state.py`, saved in `var/runs/state.json`), so a restart stays paused. `paused_until` is a usage limit's: not that one.
  - **Pause is a state of the pick (ADR 22 item 5):** `plan` in `runner/dispatch.py` takes it, and every line then waits with "paused by you", so `pick` returns None. `dry_run_plan` in `runner/loop.py` shows it too.
  - In `work_queue`, a None pick while paused neither ends the run nor sleeps to a reset (`_wait_for_reset`): it waits as `wait_for_claude` with `until` does, polling every `SWITCH_POLL_S`, its run's activity "paused by you". The wait must apply a `resume` (and the switches), as `take_switches` in `runner/requests.py` does for the switches; then it picks again.
  - Record the pause from start to resume so that "What clogged the line" (`clog` in `factory_dashboard/queries.py`) counts it under `owner` ("Stopped for you"), not under `limit`. `wait_for_claude` records a `wait` usage event, which counts as `limit`: pass `limit=False` and record a kind of its own, or mark it.
  - A job already running is never stopped: the pick runs between jobs.
- **The buttons:** Now shows "Pause after this job" while the runner runs and isn't paused. While paused, it shows "Paused by you since HH:MM" and a "Resume" button. Both go through `POST /requests`, as f5-02's worked example does; add both kinds to `KINDS` in `factory_dashboard/requests.py`.
- `uv run runner pause` and `uv run runner resume` do the same from the console, writing the request as `runner reserve` does (`_switch_request` in `runner/cli.py`).

### Done when
- a test: after a `pause` request, the runner finishes its current job, takes no other, and its activity reads "paused by you"; after `resume` it picks again
- a test: a paused runner that restarts stays paused
- a test: while paused, `pick` returns None and every line of `plan` waits with "paused by you"
- a test: the buttons post the right kinds, and Now shows the paused line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

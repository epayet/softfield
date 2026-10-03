---
id: f5-18-pause
milestone: f5-board
depends_on: [f5-01-requests-apply, f5-02-requests-route]
agent: lead
difficulty: 4
files:
  - runner/requests.py
  - runner/loop.py
  - factory_dashboard/requests.py
  - factory_dashboard/queries.py
  - factory_dashboard/templates/_partials/running.html
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_requests.py
---

### Goal
From the Overview, the owner can pause the factory: the runner finishes the job it is on, then holds until the owner resumes. They can then talk to the lead about what they saw, without the line moving on meanwhile.

### Context
Read `docs/milestones/f5-board.md` (D1–D3), `runner/requests.py` (`apply_requests`), `factory_dashboard/requests.py` (`POST /requests`, its guard and partial), `wait_for_claude` in `runner/loop.py` (how a wait is shown and recorded), and `factory_dashboard/templates/_partials/running.html` (Now). Test-first.
- **Why (owner, 2026-10-03):** "It would be good to be able to direct a milestone as it's happening if I notice something, trigger a replan from the result of the chat. Might be worth pausing while I chat about it." The chat and the replan are F6's (the planning room); this is the pause.
- **Two request kinds** in D1's table: `pause` and `resume`, with no subject and no value.
  - `apply_requests` records the pause in the runner's state file (`var/runs/state.json`), so a restart stays paused.
  - At each pick, a paused runner doesn't take the next job. It waits as `wait_for_claude` does: polling the requests, its run's `activity` set to "paused by you". Record the pause from start to resume so that "What clogged the line" (`queries.clog` in `factory_dashboard/queries.py`) counts it under `owner` ("Stopped for you"), not under `limit`. Today a `wait` usage event counts as `limit`, so use a kind of its own, or mark it.
  - A job already running is never stopped.
- **The buttons:** Now shows "Pause after this job" while the runner runs and isn't paused. While paused, it shows "Paused by you since HH:MM" and a "Resume" button. Both go through `POST /requests`, as f5-02's worked example does.
- `uv run runner pause` and `uv run runner resume` do the same from the console.

### Done when
- a test: after a `pause` request, the runner finishes its current job, takes no other, and its activity reads "paused by you"; after `resume` it picks again
- a test: a paused runner that restarts stays paused
- a test: the buttons post the right kinds, and Now shows the paused line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f138-01-ctrl-c-ends-the-run
milestone: f138-run-again-right-after-ctrl-c
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/cli.py
  - runner/loop.py
tests:
  - tests/runner/test_cli.py
---

### Goal
After a Ctrl-C (or a crash) on `softfield run`, running it again starts at once, and the interrupted job is still recovered; when a run that was killed outright still refuses a start, the refusal says how long to wait.

### Context
Read `.softfield/cards/f138-run-again-right-after-ctrl-c.md` (Decisions D1–D3), then in `runner/cli.py`: `main` (its `finally`, which calls `loop.end_open_runs`), and `_run_projects`; in `runner/loop.py`: `run_projects` (its `except KeyboardInterrupt`), `end_open_runs`, `_finish_run`, `live_run` and `LIVE`, and `open_session` (recovery reads `state.in_flight` from state.json, not the run's row).
- The cause: `main` returns `_run_projects(...)` before its `try:`, so `softfield run` never reaches the `finally` that `runner run --here` has (f2-03). A Ctrl-C mid-job leaves the busy session in `OPEN_RUNS`, its row with no `ended`, and `live_run` refuses for up to 2 minutes.
- `test_a_ctrl_c_or_a_crash_ends_the_commands_runs` in `tests/runner/test_cli.py` is the example to follow; `test_runner_pause_and_resume_write_the_dashboards_requests` shows how a test there sets `loop.now`.
- Keep `live_run`'s signature: five callers use its `run_dir`. The wait comes from a helper beside it (the newest live heartbeat of the project).

### Done when
- `cli.main(["run"])` whose `loop.run_projects` raises `KeyboardInterrupt` calls `loop.end_open_runs` once; so does one that raises another error
- a project whose last run's row has `ended` set, and whose state.json still names an `in_flight` job, is not refused by `softfield run`, and its next session still recovers the job (the existing recovery tests stay green)
- with a run whose heartbeat is 92 seconds old, `softfield run` prints `runner: a run of softfield was live at 09:31:45 and may still be: one runner at a time; if you stopped it, try again in 28 s` (the project's name, the heartbeat's local time, the seconds left of `LIVE`) and returns 1
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

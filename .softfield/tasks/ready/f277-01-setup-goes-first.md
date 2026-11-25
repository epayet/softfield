---
id: f277-01-setup-goes-first
milestone: f277-why-did-the-runner-decide-to
agent: lead
difficulty: 4
depends_on: []
files:
  - runner/loop.py
  - runner/planner_job.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A project being set up gets its setup before anything else the runner could pick, in any project, including when it was started in the middle of another project's turn.

### Context
Read "What happened" and D1 to D3 in `.softfield/cards/f277-why-did-the-runner-decide-to.md`, then `project_round`, `run_projects`, `work_queue` (the `being_set_up` lines) and `apply_owner_requests` in `runner/loop.py`, `setting_up` in `runner/planner_job.py`, and `_new_project` in `runner/requests.py`. Follow the `project_round` tests in `tests/runner/test_loop.py` (search `project_round(`) and the `SETTING_UP` set-up in `tests/runner/test_cli.py`. `runner/**` is protected: tests first.
- For D3, the logs of 2026-11-19 are in duck-ascii-test's `.softfield/var/runs/20261119-160752/` and Softfield's `.softfield/var/runs/20261119-121218/`. If they don't say why the queued-jobs pass ran Softfield's planner first, reproduce the round in a test (a session just opened, first in the list, with a `setup` row) before changing anything.

### Done when
- in `project_round`, a session whose project is being set up and has an open `setup` row runs it before any session's fast-lane turn and before any other queued job or ticket, while the owner's pause holds too
- a turn whose `apply_owner_requests` starts a project (a `NEW_PROJECT` request, `runner/requests.py`) runs no job and returns, so `run_projects` reads the projects again before the next pick
- a round with a set-up project first in the list and a Softfield planner row runs the setup, not the planner (the 16:07:52 case), and the test fails without the change
- a project not being set up is picked as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

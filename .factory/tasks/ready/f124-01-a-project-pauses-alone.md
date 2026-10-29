---
id: f124-01-a-project-pauses-alone
milestone: f124-pause-one-project-from-the-projects
difficulty: 5
depends_on: []
files:
  - runner/metrics.py
  - runner/requests.py
  - runner/loop.py
  - runner/cli.py
  - factory_dashboard/requests.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
agent: lead
---

### Goal
The owner can pause one project, and resume it, with a request: its tickets, checkpoints and reviews wait while its planning and its requests still go, and the other projects carry on.

### Context
Read `.factory/cards/f124-pause-one-project-from-the-projects.md` ("What happens today", D1 to D4).
- `projects.paused` and `set_project_paused` are in `runner/metrics.py` (V13); `_project_configs` in `runner/cli.py` drops any project with a `paused`, so `run_projects` in `runner/loop.py` closes its session and its requests are never read.
- The factory's pause: `_pause` in `runner/requests.py` sets `state.owner_pause`; `work_queue` passes `paused=` to `dispatch.pick`; `project_round` holds every project's tickets while one has it. A project's pause is that `paused=`, for that project alone; `project_round`'s factory-wide check stays as it is.
- The new kinds go in `_apply` beside `PROJECT_ORDER` (`_project_order` is the example: the database only, no clean main), and in `KINDS` of `factory_dashboard/requests.py`.
- `_print_plan` in `runner/loop.py` gives each ticket its wait; `_guide` in `runner/cli.py` prints each project's `paused`.
- `softfield doctor` (`runner/setup.py`) releases "setting up" only: leave it.

### Done when
- a `pause_project` request on a running project sets its `paused` to the time and answers "paused by you: its tickets wait after the job it is on"; again, "already paused, since HH:MM"; on a project being set up, "being set up: `softfield doctor` hands it over", its `paused` unchanged
- `resume_project` clears it and answers "resumed"; on a project not paused by you, "not paused"
- with softfield paused by you and coucou running, a round runs coucou's ticket, never softfield's; softfield's queued planner job still runs, and its requests are still applied (a resume among them)
- a project paused by you keeps its session; one "setting up" is still skipped
- while held, its activity is `Idle: paused by you since HH:MM`; `--dry-run` says its tickets are "paused by you"; a bare `softfield` says "paused by you since HH:MM"
- the dashboard's `POST /requests` takes both kinds
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f290-08-planner-job-own-module
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 5
max_diff: 6000                      # a move counts its lines twice: removed and added
depends_on: [f290-07-review-job-own-module]
commands: [cp, sed -i]
files:
  - runner/loop.py
  - runner/planner_job.py
  - runner/session.py
  - runner/requests.py
  - runner/setup.py
  - runner/planner.py
  - runner/milestone.py
  - tests/runner/test_loop.py
  - tests/runner/conftest.py
  - tests/runner/test_planner.py
  - AGENTS.md
  - runner/instructions/claude.md
  - .softfield/cards/f290-runner-loop-py-is-6-500.md
tests:
  - tests/runner/test_planner_job.py
---

### Goal
The planner's and the setup's jobs (plan branches, drafts, the auto-merge, where the work stands, naming a card) live in `runner/planner_job.py`, with their tests in `tests/runner/test_planner_job.py`; `runner/loop.py` is left the scheduler only, and nothing the runner does changes.

### Context
Read the Decisions in `.softfield/cards/f290-runner-loop-py-is-6-500.md` (D1–D8), and follow f290-07's commit (`git log -1 --stat`).
- The candidates in `runner/loop.py`: from `def _plan_branch` to the end of `def _left_on_main` (`def catch_up_plan` and `def both_added` too; `runner/requests.py` calls `loop.catch_up_plan`), `def run_planner`, `def run_setup`, `def work_stands`, `def ticket_minutes`, `def _name_card`, `def _commit_drafts`, `def _auto_merge`, applying D3. `def setting_up`, `def project_pause` and `def project_archived` stay if only the scheduler uses them.
- `runner/loop.py` imports `runner/setup.py` inside `run_setup` ("it imports the planner, which imports this"), and `runner/planner.py` reads `loop.MAIN` inside a function: once the planner job has left, check whether those imports can move to the top of their file without a cycle, and fix their comments to say what is true.
- D5: the planner test that patches `call_claude` on `loop` (`tests/runner/test_planner.py`) patches it on `session` already since f290-01; check.
- Then D8's last part: `AGENTS.md` item 5 names the runner's edges as `runner/session.py`, the `_job` modules and `runner/loop.py`, and adds one line: "A new job kind gets its own `runner/<kind>_job.py`; `runner/loop.py` only schedules." Point `runner/instructions/claude.md`'s mention of `loop.py` at the module that now calls Claude. Fix the docstring at the top of `runner/loop.py` to say it is the scheduler.
- Log the sizes as landed (each new module and test file, and `runner/loop.py`) under `## As built (f290-08)` in the card doc, one line each.
- Then D7 for each moved name.

### Done when
- `runner/planner_job.py` holds the planner and setup jobs, at most 1,800 lines, and does not import `runner/loop.py` at module level
- `runner/loop.py` is under 2,000 lines and holds no function that only one job kind calls
- the moved tests pass in `tests/runner/test_planner_job.py`, none renamed or edited beyond imports and patch targets, and every other test in `tests/runner/` passes
- `AGENTS.md` names the job modules and the one-line rule; the card doc has `## As built (f290-08)`
- no ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or `class` beside `runner/loop.py`
- all gates pass (see `docs/workflow.md`), mypy included

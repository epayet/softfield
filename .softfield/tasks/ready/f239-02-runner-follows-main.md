---
id: f239-02-runner-follows-main
milestone: f239-i-want-to-be-able-to-3
agent: lead
difficulty: 4
depends_on: [f239-01-run-config-and-stacks]
files:
  - runner/stacks.py
  - runner/loop.py
  - tests/runner/test_stacks.py
tests:
  - tests/runner/test_stacks.py
---

### Goal
A project's running app follows its main: when main moves, the runner moves the app's checkout and rebuilds the stack, and a failed rebuild leaves the old app running and says so.

### Context
Read ADR 46 items 3 and 4 and D2 and D3 in `.softfield/cards/f239-i-want-to-be-able-to-3.md`, then `stack_for` and `state` in `runner/stacks.py` (f239-01) and `_new_code` and `update_live` in `runner/loop.py`: the runner calls `update_live` when a job ends and before each pick, which is where `follow_main` belongs, for the session's project.
- `follow_main` does nothing when the checkout is already at main or the project has no `[run]`. Otherwise it moves the checkout (detached, as `update_live` does); if the app was running it runs `up -d --build` and writes the result file of D3 (`ok`, the commit, the time, the last 40 lines on failure). A stopped app's checkout still moves, and nothing starts.
- Before the rebuild, the copy of the data folder in D8: the 3 newest copies stay. If the copy fails, no rebuild: the result file says `ok: false` with the reason.
- It never raises: a failure goes to the result file and to the console with the time, as `_reinstall` does.

### Done when
- main moving on a running project's repo moves its checkout and calls `up -d --build` once
- a failed build writes `ok: false` with the tail, and `state` then says update failed while the old containers still answer
- a rebuild makes a copy of the data folder named for the new commit, and a fourth rebuild leaves 3 copies
- a failed copy writes `ok: false` and never calls `up`
- a stopped project's checkout follows main and nothing is started
- a project without `[run]`, and Softfield itself, are left alone
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

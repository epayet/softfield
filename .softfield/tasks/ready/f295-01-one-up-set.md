---
id: f295-01-one-up-set
milestone: f295-runner-requests-py-s-forget-project
difficulty: 1
depends_on: []
files:
  - runner/stacks.py
  - runner/requests.py
  - factory_dashboard/stacks_routes.py
tests:
  - tests/runner/test_stacks.py
  - tests/runner/test_requests.py
agent: lead
area: factory
---

## Goal
Keep one list of the app states that count as "up", in `runner/stacks.py`, and use it in both the Projects page's Stop/Run button and the runner's Forget guard, so the two can't drift apart.

## Context
- `runner/stacks.py`: the state words (`RUNNING`, `STARTING`, `UPDATE_FAILED`, …) are defined near the top. Add `UP` beside them, with the comment now above `UP` in `factory_dashboard/stacks_routes.py` (a crashed app is not up; a failed update left the old containers running).
- `factory_dashboard/stacks_routes.py`: drop its own `UP`; `AppRow.up` and anything else that reads it use `stacks.UP`. Leave `BROKEN` where it is: only the page uses it.
- `runner/requests.py`: `_forget_project` lists the three states inline; use `stacks.UP` instead.
- `tests/runner/test_requests.py`: `test_a_project_whose_app_runs_is_not_forgotten` loops over the three states with a comment; loop over `stacks.UP`.

## Done when
- `stacks.UP` is `(RUNNING, STARTING, UPDATE_FAILED)`, and a test in `tests/runner/test_stacks.py` checks that, including that `CRASHED` and `STOPPED` are not in it
- `factory_dashboard/stacks_routes.py` has no `UP` of its own, and no file in `runner/` or `factory_dashboard/` lists those states as a set by hand anymore
- Forget is still refused while the app is up and still goes through once it has stopped. The page's Stop/Run button doesn't change
- the listed `tests:` pass, and fail without the change
- all gates pass

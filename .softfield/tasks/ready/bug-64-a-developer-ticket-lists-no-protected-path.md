---
id: bug-64-a-developer-ticket-lists-no-protected-path
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
files:
  - runner/tasks.py
tests:
  - tests/runner/test_tasks.py
---

### Goal
Pre-flight refuses a developer ticket whose `files:` or `tests:` list a protected path, so a direction's repaired `ticket.md` can't send the developer into a file the `protected-paths` gate then rejects.

### Context
f251-01 (2026-11-16 run): the direction after two no-edit attempts added `tests/factory_dashboard/test_requests.py` to the ticket's `tests:` and told the developer to change a regex there. That file is in `.softfield/protected-paths.txt`. Pre-flight let the repaired ticket through, the developer followed it, and the third attempt failed only on `protected-paths`.
- `preflight` in `runner/tasks.py` checks `TESTS_ONLY`, `FIX_OF_FIX` and `STALE_BRANCH`, and nothing about protected paths. Add a problem, worded like those, when a ticket that isn't `agent: lead` lists a path in `files:` or `tests:` that `.softfield/protected-paths.txt` matches. It names the path and says the ticket is the lead's.
- The gate's own matching is `touching_protected` in `runner/gates.py`; use the same function, and read the patterns from the repo the ticket runs in, the way the gate does.
- `test_preflight` cases in `tests/runner/test_tasks.py` are the worked example.

### Done when
- a developer ticket listing `tests/factory_dashboard/test_requests.py` in `tests:`: the problem, naming that path
- a developer ticket listing `runner/tasks.py` in `files:`: the problem, naming that path (a glob, `runner/**`)
- the same tickets with `agent: lead`: no problem
- a developer ticket listing only `factory_dashboard/app.py` and `tests/factory_dashboard/test_app.py`: no problem
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

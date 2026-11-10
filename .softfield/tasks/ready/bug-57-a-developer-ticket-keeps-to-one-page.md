---
id: bug-57-a-developer-ticket-keeps-to-one-page
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
finding: f170-there-s-a-blocked-ticket-that-F9
files:
  - runner/tasks.py
tests:
  - tests/runner/test_tasks.py
---

### Goal
Pre-flight refuses a developer ticket whose `files:` span two pages' modules, so a ticket like f170-04 is routed to the lead before it costs three failed attempts.

### Context
Read `def preflight` in `runner/tasks.py`, and the routing rule from F143 D6 in `runner/instructions/task-writing.md`: one of the modules under `factory_dashboard/`, its test file and its template go to the developer; two pages' modules stay the lead's. Nothing checks it yet: f170-04 listed `factory_dashboard/tickets.py` and `factory_dashboard/planning.py`, spent 7.3M local tokens on three failed attempts, then escalated.
- Add a problem, as `TESTS_ONLY` is one, when a ticket that isn't `agent: lead` lists two or more of `factory_dashboard/planning.py`, `factory_dashboard/coming.py`, `factory_dashboard/thread.py`, `factory_dashboard/merges.py`, `factory_dashboard/proposal.py` and `factory_dashboard/tickets.py`.
- f210-02 (2026-11-10) was the next: a developer ticket listing `factory_dashboard/planning.py` and `factory_dashboard/thread.py`, three attempts with no edit (26–28 tool calls each, the third under a direction), done by the lead in one session. This check would have refused it.
- Checked against main on 2026-11-09 (F231): `runner/tasks.py` names none of these modules yet.
- `test_preflight` cases in `tests/runner/test_tasks.py` are the worked example; the problem's words name the modules and say the ticket is the lead's.

### Done when
- a developer ticket listing `factory_dashboard/tickets.py` and `factory_dashboard/planning.py`: the problem, naming both
- the same ticket with `agent: lead`: no problem
- a developer ticket listing one of them, its template and its test file: no problem
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

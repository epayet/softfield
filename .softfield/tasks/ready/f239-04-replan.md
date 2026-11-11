---
id: f239-04-replan
milestone: f239-i-want-to-be-able-to-3
agent: lead
difficulty: 2
depends_on: [f239-02-runner-follows-main, f239-03-run-and-stop-routes]
files:
  - .softfield/cards/f239-i-want-to-be-able-to-3.md
  - .softfield/tasks/ready/f239-05-app-row-on-projects.md
  - .softfield/tasks/ready/f239-06-logs-page.md
  - .softfield/tasks/ready/f239-07-crashed-app-needs-you.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
The developers' three tickets match what f239-01 to f239-03 built, before a developer starts on them.

### Context
Read D1 to D7 in `.softfield/cards/f239-i-want-to-be-able-to-3.md`, then runner/stacks.py (f239-01), the routes in `factory_dashboard/projects.py` and the app row partial in factory_dashboard/templates/_partials/ (f239-03) as they are on main, and the three ready tickets named in `files:`.
- Fix any name, field or path in D1 to D7 and in those tickets that differs from the code, and log what changed under a `## Replan` heading in the card doc.
- Leave the code alone: a real gap becomes a point in the log, with the ticket that will fix it.

### Done when
- every function, field and path the three tickets name exists on main
- `softfield check-tickets` passes on the three tickets
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

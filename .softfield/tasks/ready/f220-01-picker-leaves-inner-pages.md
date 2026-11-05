---
id: f220-01-picker-leaves-inner-pages
milestone: f220-if-i-m-browsing-a-certain
difficulty: 1
depends_on: []
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
Choosing a project in the picker from an inner page (a thread, a card, a ticket, a job, a run, a project's page) lands on that tab's own page for the new project, never on the same address in the other project.

### Context
Read `.softfield/cards/f220-if-i-m-browsing-a-certain.md` (D1–D3).
- `factory_dashboard/templates/base.html`: the `filters` form. Give it an `action`: `picker_to` if the page set it, else `active`. Every page already sets `active`.
- `factory_dashboard/milestones.py`: `milestones_list` adds `"picker_to": "/milestones"`, as that list lights Board but every project has it. `milestone_detail` doesn't.
- Another ticket (f132-08) may move this form into the tab strip, before or after this one: in the test, find the form by the one holding `select name="project"`, not by where it sits in the bar.
- The form keeps `method="get"`, its submit on change and its `<noscript>` button.

### Done when
- the picker's form on a thread page submits to `/planning`, on a card's page to `/board`, on a ticket's page to `/tickets`, on a job's page to `/jobs`, on a run's page to `/runs`, on a project's page to `/projects`
- on the Board, Planning, Tickets and the Overview it submits to the page's own address, and on the Milestones list to `/milestones`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

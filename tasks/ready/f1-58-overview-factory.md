---
id: f1-58-overview-factory
milestone: f1
depends_on: [f1-52-overview-live, f1-54-factory-replay]
difficulty: 5
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/static/factory.js
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview opens on the factory: the live floor of the current milestone under Needs-you, with a Now panel saying what each agent is doing and what it does next.

### Context
Read `docs/milestones/f1.md` D10 ("Where"). Follow `factory_dashboard/overview.py` with `tests/factory_dashboard/test_overview.py`, and f1-53's floor (`factory_dashboard/line.py`, `factory_dashboard/static/factory.js`, `tests/factory_dashboard/test_line.py`). Open `docs/milestones/f1-factory-mockup.html` in a browser, "Now (example)" and "3 developers (example)".
- **Order on `/`:** Needs-you (f1-52's `/live` partial, only when it has items), the floor of the current milestone at its latest moment, the Now panel, then the panels that stay (last verdict, allowance, savings, spend). The Running now and Queue panels go: the floor and the Now panel show both.
- **Live:** while a run is live, the floor and the Now panel refresh every 5 s with `/live`; a running job's crate is in its machine and the run's activity or wait shows under the floor.
- **The Now panel,** one column per machine: its name, LEAD / developer / shadow, LOCAL or CLOUD, its rating; what it is working on (ticket, role, attempt, time, tokens); then its next tickets in run order (`queries.run_order`), each "ready" or "after f1-xx". Hovering a ticket there makes its crate blink on the floor.
- **Links:** "Factory" in the top bar (the current milestone's line); each milestone page links to its line.

### Done when
- `/` shows the floor's document for the current milestone and no Running now or Queue heading
- the Now panel lists a running ticket under its machine and the next ticket in run order with its waits
- a live run's page refreshes the floor through `/live`
- the top bar has Factory; `/milestones/f1` links to `/milestones/f1/line`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

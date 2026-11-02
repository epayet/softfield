---
id: f132-05-floor-every-project
milestone: f132-the-overview-shows-the-whole-factory
agent: lead
difficulty: 6
depends_on: [f132-02-overview-live-every-project]
files:
  - factory_dashboard/line.py
  - factory_dashboard/queries.py
  - factory_dashboard/templates/_partials/line.html
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The floor, on the Overview and on `/line`, is the whole factory's: the field counts every project's cards, the shared machines carry any project's crate, each crate says its project, and the stash counts every project's merges.

### Context
Read `.softfield/cards/f132-the-overview-shows-the-whole-factory.md` (D2–D4, D9) and the Proposed floor panel of `.softfield/cards/f132-mockup/overview.html`.
- `factory_dashboard/line.py`: `live_line` and `replay` read one project through `_tickets`, `_jobs`, `trips`, `_work`, `_states`, `_field`, `_planting`, `_due_reviews`, `_config`, `_wait` and `_clog`; `queries.run_order` and `queries.clog` in `factory_dashboard/queries.py` too. Each takes the names from `every_project` (`factory_dashboard/overview.py`, f132-02) instead.
- Ticket ids are unique only inside a project: key the crates and the states by (project, ticket) wherever two projects' could meet.
- A crate's label starts with its project's plate when `many_projects` is true (f132-02's project plate partial in `factory_dashboard/templates/_partials/`, and `.proj`); the floor's legend says so in plain words.
- `_config` reads a project's `.softfield/project.toml` for its checks' names: with several projects, read each crate's own project's.
- The replay (`/line/replay`, `factory_dashboard/static/factory.js`) gets the same lists, so a replay of the morning shows travel-companion's and softfield's crates together.

### Done when
- with softfield and travel-companion: the field's counts are the sums of both projects' cards per stage, and the floor is the same for either project picked
- a running softfield job's crate sits on its machine with a "softfield" plate; travel-companion's tickets merged this morning reach the stash beside softfield's, the day's belt numbers counting both
- two projects with a ticket of the same id: two crates, one per project
- a replay over a span with both projects' jobs plays both
- one project only: no plate, and the floor reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

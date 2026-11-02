---
id: f132-03-away-every-project
milestone: f132-the-overview-shows-the-whole-factory
difficulty: 3
depends_on: [f132-02-overview-live-every-project]
files:
  - factory_dashboard/queries.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/away.html
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_queries.py
---

### Goal
While you were away, on the Overview, counts and lists what every project did in the span, each row with its project's plate.

### Context
Read `.softfield/cards/f132-the-overview-shows-the-whole-factory.md` (D2–D4) and the Proposed "While you were away" panel of `.softfield/cards/f132-mockup/overview.html`.
- `away` and `Away` in `factory_dashboard/queries.py`; `overview` and `away_partial` in `factory_dashboard/overview.py` call it for the picked project.
- `every_project` (f132-02, in `factory_dashboard/overview.py`) gives the projects; the plate is f132-02's project plate partial in `factory_dashboard/templates/_partials/`, shown when `many_projects` is true. Follow how f132-02 uses both in `factory_dashboard/templates/_partials/queue.html`.
- The simplest way: `away` per project, then one `Away` whose counts and dollars are the sums and whose rows are every project's, latest finish first, each knowing its project.
- Each row's ticket link carries its own `?project=`.

### Done when
- since 20:00, softfield with 11 merged and $53.39 on Claude, travel-companion with 5 merged and $34.61: the line reads "16 merged, …, $88.00 on Claude" on the Overview of either project
- the rows of both projects are one list, latest finish first, each with its plate and a link to its own project's ticket page
- choosing another span (`/away`) gives the same sums for any picked project
- one project only: no plate, and the panel reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

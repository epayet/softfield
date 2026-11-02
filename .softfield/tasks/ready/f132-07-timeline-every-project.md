---
id: f132-07-timeline-every-project
milestone: f132-the-overview-shows-the-whole-factory
difficulty: 3
depends_on: [f132-02-overview-live-every-project, f132-04-savings-on-project-page]
files:
  - factory_dashboard/timeline.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/timeline.html
tests:
  - tests/factory_dashboard/test_timeline.py
---

### Goal
The Timeline's agent lanes carry every project's jobs, each bar naming its project, and open on the last 24 hours instead of one card.

### Context
Read `.softfield/cards/f132-the-overview-shows-the-whole-factory.md` ("What happens today", D2–D4).
- `timeline_data` and `timeline_page` in `factory_dashboard/timeline.py`: today the page opens filtered on `current_milestone`, the newest plant (on 2026-10-20 a card merged away, so the lanes were empty).
- With no filter, the page shows the jobs that started in the last 24 hours of every project in `every_project` (`factory_dashboard/overview.py`, f132-02); the milestone and run filters keep working, and the milestone list names each milestone's project when `many_projects` is true.
- A bar's tooltip and link carry its project (`?project=` on the job's link).
- After this, nothing calls `current_milestone` (f132-04 removed the Overview's use): delete it from `factory_dashboard/overview.py`, with its tests.

### Done when
- with softfield and travel-companion jobs this morning: `/timeline` shows both projects' bars in their agents' lanes, for either project picked, and none older than 24 hours
- `?milestone=` of a travel-companion milestone shows its bars only
- each bar's link opens its job with its own project
- `current_milestone` is gone
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

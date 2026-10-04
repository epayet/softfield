---
id: f9-04-timeline-milestone-filter
milestone: f9-line-polish
depends_on: []
difficulty: 2
files:
  - factory_dashboard/timeline.py
  - factory_dashboard/templates/timeline.html
tests:
  - tests/factory_dashboard/test_timeline.py
---

### Goal
The Timeline's milestone filter shows the milestone picked, and "All milestones" shows every milestone's jobs.

### Context
Read the route in `factory_dashboard/timeline.py` (`filter_milestone = milestone or default_milestone`), the filter form in `factory_dashboard/templates/timeline.html`, and `tests/factory_dashboard/test_timeline.py`.
- The owner (2026-10-04): "changing milestone in the timeline view doesn't work".
- An empty `milestone` is "All milestones" and falls back to the current milestone today, so "All" can't be chosen. Only a request with no `milestone` at all takes the default. The form also drops `?project=`; keep it, as the Tickets page's links do.

### Done when
- `?milestone=` (empty) returns jobs of two milestones; `?milestone=f2` only F2's; no parameter, the current milestone's
- the form keeps `project` when it submits
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

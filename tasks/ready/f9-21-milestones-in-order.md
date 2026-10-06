---
id: f9-21-milestones-in-order
milestone: f9-line-polish
depends_on: []
difficulty: 3
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The Milestones page lists the milestones in progress first, then those not started (the next to run first), then the finished ones (the most recently finished first).

### Context
Read `factory_dashboard/milestones.py` (the list's query and `_sort_key`) and `tests/factory_dashboard/test_milestones.py` (`test_milestones_shows_newest_first`, which this replaces, and its fixtures).
- What the database holds (2026-10-06): `milestones.status` is `done` once signed off, and `ended` is set then. `state` and `started` are not reliable: F6, F8 and F9 say `ready` while being built, and most `f` milestones have no `started`. So group by the work, from `jobs` (`milestone_id`, `started`):
  1. in progress: not done, and at least one job: the latest job's `started` first;
  2. not started: not done, no job: by `priority` (lower first; NULL counts as 100), then key, the order the runner takes them;
  3. done: `status` done, the latest `ended` first (none last).
- The owner (2026-10-06): "the ones being worked on, then the ones planned next, then the finished ones, the most recent first".

### Done when
- with two milestones of each group in the fixtures, the page lists the in-progress ones by their latest job, then the not-started ones by priority, then the done ones by end date
- a test fails if two done milestones come oldest first, or if a ready milestone with priority 2 comes after one with priority 5
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f124-03-next-in-line-says-paused
milestone: f124-pause-one-project-from-the-projects
difficulty: 2
depends_on: [f124-01-a-project-pauses-alone, f132-02-overview-live-every-project]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Next in line never lists a paused project's tickets as next: it gives that project one line, "Paused by you since HH:MM", as F132 gives a passed-over project one.

### Context
Read D1 and D4 of `.factory/cards/f124-pause-one-project-from-the-projects.md` and D5 of `.factory/cards/f132-the-overview-shows-the-whole-factory.md` (the "Passed over: …" line, which f132-02 built in `factory_dashboard/overview.py`).
- `paused_by_you` in `runner/metrics.py` gives the time a project was paused by you, None otherwise; the rows come from `projects_in_order`.
- Its planning replies stay in the list: a project's pause doesn't hold them.

### Done when
- with softfield paused by you since 21:40 and coucou running, Next in line lists coucou's tickets, and for softfield the one line "Paused by you since 21:40: its tickets wait"
- softfield's queued planning reply is still listed first
- with no project paused, Next in line is as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

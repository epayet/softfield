---
id: f1-56-timeline-and-plan-tabs
milestone: f1
depends_on: [f1-53-factory-line]
difficulty: 6
files:
  - factory_dashboard/line.py
  - factory_dashboard/timeline.py
  - factory_dashboard/templates/line.html
  - factory_dashboard/templates/timeline.html
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_timeline.py
---

### Goal
The factory line gets two more tabs, Production timeline and Plan vs actual, and the separate `/timeline` page becomes the first of them.

### Context
Read `docs/milestones/f1.md` D10. Follow f1-53's worked example (`factory_dashboard/line.py`, `factory_dashboard/static/factory.js`, `factory_dashboard/templates/line.html`, `tests/factory_dashboard/test_line.py`) and read `factory_dashboard/timeline.py` (`timeline_data`, the route) with `tests/factory_dashboard/test_timeline.py`. Open `docs/milestones/f1-factory-mockup.html` in a browser, tabs "Production timeline" and "Plan vs actual".
- **Production timeline:** one lane per agent ("the lead on Opus", "the lead on Sonnet", each developer), one block per job labelled with its ticket's number, a failed attempt with a red top edge, Claude limit windows hatched across the lanes. Idle stretches over 40 min are drawn shorter with their real length written on them (the document's idle stretches).
- **Plan vs actual,** one row per ticket that had jobs, sorted by planned start:
  - planned: the earliest each ticket could start if every machine were always free, from `depends_on` and its real work time (the sum of its jobs, at least 5 min)
  - actual: from its first job to its last, its jobs as blocks, and the time it waited while a Claude limit window was on hatched red ("waited for Claude's limit")
  - totals above: the shortest possible by dependencies, start to finish, and the time waited for Claude
- The plan and the waits are computed in `factory_dashboard/line.py`, into the document.
- **`/timeline` redirects** to the current milestone's line, Production timeline tab, and leaves the top bar's tabs; `timeline_data` may be reused or folded in.

### Done when
- for a fixture where b needs a, each taking 30 min of work, b's planned start is a's planned end
- a ticket whose job came right after a limit window shows that wait, and the total counts it
- an idle gap of 3 h between jobs is shortened and labelled "3 h 00"
- `/timeline` answers with a redirect to the line; the top bar no longer lists Timeline
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

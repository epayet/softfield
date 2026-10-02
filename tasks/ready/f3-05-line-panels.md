---
id: f3-05-line-panels
milestone: f3
depends_on: [f3-01-factory-line, f3-04-clog-today]
difficulty: 3
files:
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/templates/overview.html
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Under the floor, the Overview shows Now (the running ticket's goal and the next three in line) and "What clogged the line today". The old Running now and Queue panels go.

### Context
Read the line mock-up (`docs/milestones/f3-line-mockup/Line.dc.html` and `docs/milestones/f3-line-mockup/LinePhone.dc.html`: read the SVG and the data in each file's script, not pages to open) (the panels under the floor), `factory_dashboard/line.py` (`live_line`: Now, the next three and `clog`), `factory_dashboard/templates/_partials/live.html`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`.
- **Now:** the attempt and minutes, the ticket id, the agent and its harness, the goal in full, "read N tokens · M turns", then "Next in line": three rows of id, goal and who. When a run waits, say what for and until when, with the waiting ticket's goal (as F4 did).
- **What clogged the line today:** the four numbers from `clog`, labelled in plain words, plus one line naming the biggest.
- Remove the `#running` and `#queue` sections. Update the tests that asserted on them so they read the new panels. That's a behaviour this ticket changes, so it may.

### Done when
- with a working job, Now shows its goal and the next three tickets' goals, asserted within the panel
- the clog panel shows the four numbers with their labels
- the page has no `#running` or `#queue` section
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

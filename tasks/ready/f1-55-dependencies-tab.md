---
id: f1-55-dependencies-tab
milestone: f1
depends_on: [f1-53-factory-line]
difficulty: 5
files:
  - factory_dashboard/line.py
  - factory_dashboard/templates/line.html
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The factory line has a Dependencies tab: the milestone's tickets top to bottom in dependency order, each saying whether it is a lead or developer ticket and who worked on it.

### Context
Read `docs/milestones/f1.md` D10. Follow f1-53's worked example: `factory_dashboard/line.py`, `factory_dashboard/static/factory.js`, `factory_dashboard/templates/line.html` and `tests/factory_dashboard/test_line.py`. Open `docs/milestones/f1-factory-mockup.html` in a browser, tab "Dependencies".
- **Rows are steps:** a ticket sits one row below the last ticket it depends on (row 1: no dependencies in the milestone).
- **Links:** only direct ones (25 needs 24 and 24 needs 21: no 21→25 link), and drawn only between neighbouring rows, with an arrowhead; a ticket that also waits for something further up says "also after 42, 49 (further up)".
- **Each box:** a LEAD or DEV badge, the ticket's number and name, then one mark per job in the agent's colour (a failed one outlined red) and "by Qwen ×2 → Opus", up to the slider's time; "can start now" or "not started" before its first job.
- **Hover a box:** it and everything it needs (amber) and everything it unblocks (blue) stay lit, the rest fades.
- **The rows and links are computed in `factory_dashboard/line.py`** and added to the document; `factory_dashboard/static/factory.js` only draws them.

### Done when
- for a fixture where c needs b and b needs a, the document puts a, b, c on rows 1, 2, 3 and has no a→c link
- a ticket depending on a row two above lists it as "also after"
- the box of a ticket worked by Qwen twice then Opus reads "by Qwen ×2 → Opus" and shows three marks
- hovering a box lights its upstream and downstream (browser test)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

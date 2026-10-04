---
id: f3-30-phone-top-bar
milestone: f3
depends_on: []
difficulty: 3
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
On a phone the top bar is two short lines, the title and one row of tabs that scrolls sideways, so the sticky bar no longer covers a quarter of the screen and Now starts near the top.

### Context
Read `factory_dashboard/templates/base.html` (the top bar) and the top bar rules in `factory_dashboard/static/dashboard.css` (`header.bar`, `.bar-top`, `.brand`, `.filters`, `nav.tabs`), and the browser tests in `tests/factory_dashboard/test_app.py`. The picture: the top of `docs/milestones/f3-line-mockup/LinePhone.dc.html` (one title line and the hazard stripe) and the tab segment of `docs/milestones/f5-board-mockup/Main.dc.html`.
- **What the review saw (f3-22, `var/shots/f3-22/phone-390-dark-fold.png`, at 390 px):** the eight tabs wrap onto three rows, the project filter takes its own line, and the host address follows the title: the bar is about 210 px tall, and it is sticky (`position: sticky`), so it covers that much of every scrolled screen.
- **Under 640 px only:**
  - the title and the project filter share one line; the host address (`.brand small`) is hidden;
  - the tabs stay one row that scrolls sideways (`overflow-x: auto`, no wrap), the current tab scrolled into view;
  - the hazard stripe stays.
- Desktop keeps today's bar. Every tab keeps its link and `aria-current`, and the filter keeps `?project=`.

### Done when
- a browser test at 390 px: `header.bar` is at most 110 px tall, `nav.tabs` is one row (every tab has the same top) and scrolls sideways, and the current tab is within the visible width
- a browser test at 1440 px: the bar is as today (the host address shows, the tabs fit without scrolling)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f3-19-crate-details
milestone: f3
depends_on: [f3-18-now-first]
difficulty: 4
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/templates/_partials/line.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
A click or a tap on any crate on the floor opens a small card under the floor that says which ticket it is. The card links to the ticket's page.

### Context
Read `factory_dashboard/static/factory.js`: `queue`, `machine` and `merged` draw the crates as `<g data-crate="…">` with a `<title>`. Then read `factory_dashboard/templates/_partials/line.html` and the browser tests in `tests/factory_dashboard/test_line.py`.
- **Why (owner, 2026-10-03):** "I cannot click on the tickets in the queue so I don't know what they are. In the mock-up I could." Today a crate only has a hover tooltip, so a phone shows nothing at all.
- **The card** is plain HTML, not SVG. Put a `<div id="crate-card" hidden>` right after the floor in `factory_dashboard/templates/_partials/line.html`. It shows what the document already holds for that crate:
  - the ticket id, as a link to `/tickets/<id>` (keep the page's `?project=`);
  - its title;
  - lead or developer;
  - what it waits for, for a queued crate (`waits`);
  - the agent, attempt and minutes, for a crate on a machine.

  A batch crate (a checkpoint or review, no ticket) shows its role and no link.
- **Clicks:** one listener on the floor's wrapper, which finds the `[data-crate]` that was clicked. A single listener keeps working after every redraw (f3-17). Each crate gets `tabindex="0"` and `role="button"`; Enter opens the card, and Escape or a click outside the crates closes it. A refresh that redraws the floor leaves an open card open.
- Do the same on the phone floor (`svg#floor-phone`).

### Done when
- a browser test: clicking a queued crate shows `#crate-card` with its ticket id linking to `/tickets/<id>` and its title; Escape hides it
- a browser test at 390 px wide: tapping a crate on the phone floor shows the card
- a browser test: the card stays open across a live refresh
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

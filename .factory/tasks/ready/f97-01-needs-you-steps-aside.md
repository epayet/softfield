---
id: f97-01-needs-you-steps-aside
milestone: f97-given-that-the-planning-board-has
difficulty: 3
depends_on: [f132-02-overview-live-every-project, f132-04-savings-on-project-page]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/needs_you.html
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview, Now is the first panel: Needs you moves to a box at the bottom of the page, each desk shrinks to one plate with its count, and only what stops the line shows inside Now.

### Context
Read `.factory/cards/f97-given-that-the-planning-board-has.md` (D1–D5) and build the Proposed side of `.factory/cards/f97-mockup/overview.html`: the bottom box and the "Line stopped" strip in Now.
- `factory_dashboard/templates/overview.html`: the Overview's single poller is the `#live-needs-you` div at the top (it polls `/live`, selects `#needs-you` and `#live-facts` into itself, and swaps `#now`, `#queue`, `#allowance` out of band). Move that div, as it is, to the end of the page, after While you were away; keep its ids and attributes, since `factory_dashboard/static/notify.js` and the top bar's Planning count read what it polls.
- `factory_dashboard/overview.py`, `_live_context`: f132-02 (built before this) makes Needs you list one desk line per project with its plate, count, top three and "Open ›", and every project's other needs. Split them for the templates:
  - the desks: per project with something on its desk, its name, its count and the link to its `/planning?project=<name>`; drawn in `factory_dashboard/templates/_partials/needs_you.html` as one plate each (the count, the project plate partial f132-02 adds, when there are several projects, "desk ›"), no titles;
  - the line stops: the needs of kind `runner`, `queue` and `runner.loop.MAIN_RED_KIND` (`"main-red"`), passed as `line_stops` and drawn at the top of Now in `factory_dashboard/templates/_partials/running.html` as the mock-up's strip ("Line stopped", the plate, the need's text and its command or ticket as Needs you draws them today); they leave Needs you;
  - everything else (an ADR, Claude's allowance, a review that stopped, any other kind) stays in Needs you, under the desks, as drawn today.
- `#needs-you` still shows only when it holds something.
- `notices` and `data-notices` (the phone notifications) and `planning_count` (the tab's count) don't change.
- The strip's colour is `--fail` and the box's top edge the hazard stripe: new classes go in `factory_dashboard/static/dashboard.css` beside `.panel.needs`, in the existing tokens only.

### Done when
- the Overview's first panel is Now, and Needs you is the last panel on the page
- with 25 items on softfield's desk and 1 on travel-companion's, Needs you shows two desk plates, "25" and "1", each linking to its project's Planning room, and no desk item's title
- an open `reserve` item shows under the desk plates with its text, as today
- a runner whose heartbeat stopped mid-job shows as "Line stopped" at the top of Now, and not in Needs you; the same for an idle queue and a `main-red` item
- with no desk items and no other needs, the page has no Needs you
- the `data-notices` of `/live` are the same as before the change for the same data
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

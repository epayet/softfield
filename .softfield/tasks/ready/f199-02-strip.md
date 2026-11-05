---
id: f199-02-strip
milestone: f199-let-s-improve-the-factory-floor
difficulty: 5
depends_on: [f199-01-the-map]
files:
  - factory_dashboard/line.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/strip.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The Overview shows the floor as a strip under Now and the Queue: one belt, six stops, one line saying what runs, and a button to open the map.

### Context
The picture to build: the strip in Proposed of `.softfield/cards/f199-mockup/floor.html`, with its CSS under "the strip" and its three moments. Decision D6 in `.softfield/cards/f199-let-s-improve-the-factory-floor.md` gives the shape of `glance`.
- The example to follow: `factory_dashboard/templates/_partials/running.html` and how `#now` refreshes through `/live` (`hx-select-oob` in `factory_dashboard/templates/overview.html`, `_live_context` in `factory_dashboard/overview.py`, which already calls `live_line`).
- `glance(doc)` is a plain function of the document, in `factory_dashboard/line.py`: no query of its own, and no ticket title or card title in what it returns.
- The six stops, in order: Planted, Queue, the machines (one small square per machine; the working one's colour; the name of the one working, cut to 8 characters, as its label), Checks (a light), Merged today, Ripe (hazard edge when above zero).
- The strip goes between the row of Now and the Queue and the allowance. The old floor stays below it until f199-03.
- Every stop and the button link to `/floor`. Colours from the tokens in `factory_dashboard/static/dashboard.css` only.

### Done when
- `glance` on a document with Opus working on a planner job: its status words name Opus and the job; on a document with a `wait`: the wait's words, kind `clog`; with nothing running: "nothing is running"
- `glance`'s result holds no card or ticket title
- at 390 px wide: the strip is at most 200 px tall, all six stops in one row, nothing cut off or overflowing, each stop at least 44 px wide (a browser test)
- at 1440 px wide: the same six stops in one row
- a tap on a stop or on "Open the map" goes to `/floor`
- the strip's status changes without a reload when `/live` brings a new job
- light and dark themes both readable (a browser test reads the colours, as the phone floor test does)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

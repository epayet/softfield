---
id: f199-04-map-taps
milestone: f199-let-s-improve-the-factory-floor
difficulty: 3
depends_on: [f199-01-the-map]
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
A tap on anything on the map says what it is, in plain words, and links to where it lives.

### Context
The words and the behaviour: `WHAT` and the click handler at the end of `.softfield/cards/f199-mockup/floor.html`. The example to follow: `showSeeds`, `fillCard` and the click listener in `factory_dashboard/static/factory.js`, which fill `#crate-card` with nodes and text, never HTML.
- Seed: the set-aside list `showSeeds` already gives, plus a link to `/board`. Sprouting: a link to `/planning`. Planted: every card of `doc.field.planted` with its merged count, each a link to `/milestones/<key>`. Queue: the first ten crates, and a link to `/tickets`. Ripe: each card, a link to its page. Harvested: the latest, and a link to `/board`.
- A machine: its name, where it runs, its rating, what it works on, and a link to `/agents`.
- A belt: its `label` from the document, and today's count. A crate keeps the card it has.
- Links carry `project_query()`, as the others do.

### Done when
- a tap or Enter on each station, machine and belt opens the card with its words; Escape or a tap elsewhere closes it, as the crate card does
- Planted lists 57 cards when there are 57, in the board's order, each a link to its page
- a belt's card says its words, for instance "your sign-off" and "7 went this way today"
- the card stays open over the 5-second refresh, showing the new values
- on a phone each target is at least 44 px on screen or sits inside a larger station that opens the same card
- a title holding markup shows as text
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

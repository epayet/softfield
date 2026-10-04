---
id: f9-03-field-links
milestone: f9-line-polish
depends_on: []
difficulty: 3
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
Tapping a planted row opens its milestone's page, and tapping the seeds opens the Set aside tickets.

### Context
Read `rows`, `seeds` and `showCard` in `factory_dashboard/static/factory.js` (a crate already opens a card on a tap), and the browser tests in `tests/factory_dashboard/test_line.py`.
- The owner (2026-10-04): "linking the planted rows to the more details would be good, same for the seeds".
- A planted row (`data-row` holds the milestone key) links to `/milestones/<key>`; the seeds' hopper links to `/tickets#later`. Both keep the page's `?project=` query, as the crate card's link does.
- Use an SVG `<a>` around the row's group, so a keyboard reaches it too, with a `title` saying where it goes.

### Done when
- a browser test: clicking a planted row lands on that milestone's page, and clicking the seeds lands on `/tickets` at the Set aside panel, both with `?project=` kept
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

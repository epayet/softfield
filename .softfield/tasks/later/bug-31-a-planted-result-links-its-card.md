---
id: bug-31-a-planted-result-links-its-card
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 58
finding: f48-F3
files:
  - factory_dashboard/templates/_partials/request.html
tests:
  - tests/factory_dashboard/test_requests.py
---

### Goal
A plant's result ("planted .softfield/cards/….md", "planted already: .softfield/cards/….md") links to the card's thread, as F48's Outcome says.

### Context
Read `factory_dashboard/templates/_partials/request.html` and `GET /requests/{id}` in `factory_dashboard/requests.py`, which renders it; the plant's result words are written in `runner/requests.py` (`_plant`). Lead ticket: `tests/factory_dashboard/test_requests.py` is protected.
- Today the result shows as plain text, and only while the owner stays on the page.
- When a done result names a card doc under `.softfield/cards/`, draw the card's key as a link to `/planning/<key>` (the short key, as the board's links use); a `docs/…` result and every other result stay plain text.

### Done when
- a plant done with "planted .softfield/cards/f88-add-to-lead-memory-that-new.md" shows a link to `/planning/f88`
- "planted already: .softfield/cards/f12.md" links to `/planning/f12`
- a refusal or a `docs/…` result shows as today, with no link
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

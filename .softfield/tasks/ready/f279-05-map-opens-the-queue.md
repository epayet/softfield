---
id: f279-05-map-opens-the-queue
milestone: f279-i-would-like-to-be-able
difficulty: 2
depends_on: [f279-03-the-queue-page, f199-04-map-taps]
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/templates/floor.html
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On the map (`/floor`), the queue station's tap says how many wait and opens The queue.

### Context
Read `.softfield/cards/f279-i-would-like-to-be-able.md` (D8) and `.softfield/cards/f199-let-s-improve-the-factory-floor.md` (D5, the taps of f199-04).
- f199-04 made every station say what it is on a tap, in `factory_dashboard/static/factory.js`. The queue station's note gains one link, "The whole queue ›", to `/queue`; nothing else on the map changes.

### Done when
- tapping the queue station shows its count and a link that opens `/queue`
- the other stations' taps read as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

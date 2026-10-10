---
id: f28-01-pause-survives-the-refresh
milestone: f28-the-first-time-i-clicked-on
difficulty: 4
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/templates/base.html
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The top bar's Pause or Resume keeps showing what was asked until the runner's state agrees, instead of a 5 s refresh putting the old words and button back; a failed post says so.

### Context
Read `factory_dashboard/templates/base.html` (its script and `#live-poll`) and `factory_dashboard/templates/_partials/bar_status.html`.
- The owner (2026-10-07): "the first time i clicked on the pause button nothing happened, but then eventually it worked". A `/live` poll that started before the request was stored swaps in `#factory-status` out of band with the old state; the post itself can wait up to 10 s on the database.
- D1: after a click, remember the kind asked. On `htmx:oobBeforeSwap` for `#factory-status`, while the incoming fragment's button posts that same kind (its `hx-vals`), set `event.detail.shouldSwap = false`. The first fragment whose button differs or is gone is swapped in, and the memory is cleared.
- D2: on `htmx:responseError` or `htmx:sendError` for that post, show "Didn't reach the factory: try again" in the status pill, clear the memory, and let the next poll swap in the bar with its button.
- `test_pause_in_the_top_bar_shows_pausing_at_once_and_posts_a_pause` in `tests/factory_dashboard/test_app.py` is the example; it aborts `/live`, which hid this bug. Keep it, and add tests that serve a stale `/live` instead.

### Done when
- a browser test: after Pause, a `/live` answer still showing "Running" and Pause leaves "Pausing after this job" and no button; a later `/live` with "Pausing after this job" and Resume is swapped in
- the same for Resume: a stale "Paused by you" bar doesn't replace "Resuming…"
- a browser test: a refused post (500) shows "Didn't reach the factory: try again", and the next `/live` puts the Pause button back
- without a click, polls swap the bar as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

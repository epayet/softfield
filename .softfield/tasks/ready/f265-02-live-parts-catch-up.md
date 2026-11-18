---
id: f265-02-live-parts-catch-up
milestone: f265-the-factory-now-section-in-planning
agent: lead
difficulty: 4
depends_on: [f265-01-tiles-refresh]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_coming.py
---

### Goal
The Planning page's live parts stop missing changes: a lead reply, an approval or an archive shows on the desk within a poll even while the owner scrolls, and at once when they come Back to the page, while what they type is never redrawn.

### Context
Read the Notes (the owner's second message and the code reading under it), Done when and D5–D7 in `.softfield/cards/f265-the-factory-now-section-in-planning.md`.
- `window.liveIdle` and the scroll listener are in `factory_dashboard/templates/base.html`. The desk's polls are `#live-desk` and `#live-desk-coming` in `factory_dashboard/templates/planning.html` (after f265-01, `#live-desk` also carries the tiles). The thread's own poll is the `setInterval` in `factory_dashboard/templates/thread.html`.
- Test first. In a browser (`_open(page, serve())`, the `LIVE` wait and `_lead_says` in `tests/factory_dashboard/test_planning.py`), write the owner's cases and show at least one fails on main before changing anything:
  1. the desk is scrolled (a scroll event every 2 s) while a lead reply lands: the card's box loses `on-its-way` within a poll after the scrolling stops;
  2. open a card's proposal page from the desk, store its approval (or an archive) the way the existing tests do, go Back: the item shows on its way or gone without a reload;
  3. a note half typed in the Plant box survives every poll and every `live-resume`.
  If none fails, write what you found in the card doc's Notes and stop at the scroll hold and the catch-up (D5, D6), each with its own test.
- `live-resume`: one event on `document`; send it when liveIdle turns from false to true (a 1 s check) and on `pageshow` with `persisted`, and on `visibilitychange` to visible. In htmx, a second trigger is added with a comma: `hx-trigger="every 5s [window.liveIdle()], live-resume from:document"`.
- Keep `test_desk_has_a_poll_wrapper_with_correct_attributes` and the `liveIdle` tests in `tests/factory_dashboard/test_coming.py` passing; change an assertion only where it pinned the 10 s or the exact trigger string, and say which in the commit.

### Done when
- the owner's cases above are browser tests in the listed test files, and pass
- `liveIdle()` is false within 2 s of a scroll and true again 2 s after the last one; it stays false while a field has focus, holds unsent text, sits in an open fold, or text is selected
- the planning page's two poll wrappers poll on `live-resume` too, and a `live-resume` while the owner types redraws nothing
- the thread page's poll also runs once on `live-resume`
- the listed `tests:` pass, and the new ones fail without the change
- all gates pass (see `docs/workflow.md`)

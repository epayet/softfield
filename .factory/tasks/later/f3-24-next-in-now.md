---
id: f3-24-next-in-now
milestone: f3
depends_on: []
difficulty: 3
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Now names the next three tickets under the running one, and the separate Queue panel goes: the floor's queue hopper already shows the rest, so the floor comes up a screen.

### Context
Read `factory_dashboard/templates/overview.html`, `factory_dashboard/templates/_partials/running.html` (Now), `factory_dashboard/templates/_partials/queue.html`, `factory_dashboard/templates/_partials/live.html`, and the order and queue tests in `tests/factory_dashboard/test_overview.py` (`test_the_overview_shows_every_panel_in_order`). The picture: the Now panel of `.factory/cards/f3-line-mockup/Line.dc.html` ("NEXT IN LINE" under the running ticket) and of `.factory/cards/f3-line-mockup/LinePhone.dc.html` ("next: …" in one line).
- **Why:** `.factory/cards/f3.md` D11 says "Running now and the Queue panels go; their content moves into the floor and the Now panel". The Queue panel is still beside Now; on a phone it pushes the floor two screens down (`var/shots/f3-22/phone-390-dark-full.png`).
- **Now, after the running ticket's lines:** "Next in line" with the same three rows as today's Queue panel (number, ticket link, title, "the lead" or "a developer", or "a batch"), and one line "N tickets waiting. Drain it with `<the drain command>`" (or "The queue is empty."). Now still refreshes every 5 s through `/live`, so the next three come from the same context that fills Now.
- **The Queue panel goes:** `#live-queue` and `#queue` leave the Overview. In the order test, `queue` comes out; nothing else moves.

### Done when
- `/` has no `#queue` section; `#now` holds "Next in line" with the three tickets in run order, each a link, and the waiting count
- with nothing running, Now still shows the next three and the count; with an empty queue, "The queue is empty."
- `/live` returns the same next three inside `#now`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

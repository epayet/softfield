---
id: f42-01-review-page-room
milestone: f42-the-space-for-me-to-scroll
difficulty: 3
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
The review page gives its room to what the owner reads: a mock-up opens full screen, and on a phone the dock "Your review" is one row.

### Context
Read `factory_dashboard/templates/proposal.html` (the `#mockup` iframe and the `.dock` section), the planning-room phone rules in `factory_dashboard/static/dashboard.css` (`.deck-nav`, `.dock-host`, `.dock`), `def mockup_file` in `factory_dashboard/planning.py`, and in `tests/factory_dashboard/test_planning.py` `test_the_mockup_route_serves_the_plan_branchs_mockup_and_nothing_else` and `test_on_a_phone_one_point_shows_at_a_time`. Why: `docs/milestones/f42-the-space-for-me-to-scroll.md`.
- **The mock-up:** a link "Open the mock-up" to the same URL as the iframe's `src`, `target="_blank"` with `rel="noopener"`, at least 44 px tall. Opened on its own, the route's CSP (`sandbox allow-scripts`) already keeps it in an origin of its own: change nothing in `factory_dashboard/planning.py`.
  - under 640 px the iframe is not shown, only the link;
  - from 640 px the iframe stays, `height: max(480px, calc(100dvh - 220px))`, with the link above it.
- **The dock, under 640 px only:** the count and the button side by side on one row; its `h2` hidden; `#review-status` hidden while it holds its standing sentence, shown again once a request's answer is swapped into it. From 640 px the dock is as today.
- Keep every id the tests and scripts use (`#send-back`, `#primary`, `#review-count`, `#review-status`).

### Done when
- at 390 × 844 a mock-up review shows no iframe and an "Open the mock-up" link, at least 44 px tall, whose `href` is the mock-up's route and which opens a new tab
- at 1024 px the iframe shows, at least 480 px tall, with the same link
- at 390 × 844 the dock is at most 72 px tall and still holds the count and the button, Send still in view at the bottom (the existing test's check)
- after sending, the request's answer shows in the dock at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

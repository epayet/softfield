---
id: f31-04-what-to-do-now
milestone: f31-when-i-click-on-approve-plan
difficulty: 6
depends_on: [f31-02-review-states, f31-03-point-outcomes]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A thread shows its open proposals right under the lead's latest reply as "What to do now", with their buttons, and draws each point by its outcome.

### Context
Waits in `.factory/tasks/later/` for the owner's OK on the mock-up (owner.md: mock-ups before UI tickets); the lead adds the mock-up's path here before queueing it.
Read `.factory/cards/f31-when-i-click-on-approve-plan.md` D4, D5 and D6, `factory_dashboard/templates/thread.html` (the points' `li.point`, the `#proposals` aside), and in `factory_dashboard/planning.py` `_messages`, `_proposals` and `_KIND_COLOR`.
- The buttons are f31-02's, for the same states.
- An F-number in a message's text or a point (`F22`) becomes a link to `/planning/f22` with the card's title as its text after the number ("F22, Archive at the bottom"); a number with no card stays as it is.

### Done when
- the open proposals show under the latest lead reply, above the reply box, at 390 px and 1440 px, with their state and buttons; the aside is gone
- an `info` point is a plain numbered line with a Comment… link; a `ticket`, `adr` or `mockup` point is a box with its kind's colour and a link to its proposal; a `question` point has the hazard colour; a point without outcome shows as today
- `F22` in a reply links to F22's thread and shows its title
- the layout check passes at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

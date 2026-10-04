---
id: f3-31-replay-bar-when-replaying
milestone: f9-line-polish
depends_on: []
difficulty: 2
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On a phone, the replay bar sticks to the bottom of the screen only while a replay is on; the rest of the time it sits in its place under the floor and covers nothing.

### Context
Read the replay bar rules in `factory_dashboard/static/dashboard.css` (`.replay`, `.replay-controls`, the `max-width: 639px` block), the replay bar in `factory_dashboard/templates/overview.html`, `startReplay` in `factory_dashboard/static/factory.js`, and, in `tests/factory_dashboard/test_line.py`, `test_on_a_phone_the_replay_bar_sticks_to_the_bottom_with_44_px_controls` and `start_replay`.
- **What the review saw (f3-22, `var/shots/f3-22/phone-390-dark-fold.png`):** on opening the page, the "Replay" button and the span choice sit over the bottom 70 px of Now and the Queue, before the owner has asked for a replay. The phone mock-up (`docs/milestones/f3-line-mockup/LinePhone.dc.html`) has no bar over the live page.
- **The rule:** the bar is sticky under 640 px while `#replay-controls` is shown (a replay started), and is an ordinary panel after "Back to live" and before any replay. Its controls stay at least 44 px.
- The existing sticky test is f3-07's: change it to start a replay first, and add the not-replaying case.

### Done when
- a browser test at 390 px: before any replay, `#replay` is not sticky (its computed `position` is not `sticky`)
- after "Replay": it is sticky at the bottom with 44 px controls, as f3-07's test checks; after "Back to live" it is not sticky again
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

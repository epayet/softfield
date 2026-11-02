---
id: bug-28-a-signed-off-review-folds-away
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 55
finding: f30-on-conversations-i-want-to-the-F3
files:
  - factory_dashboard/templates/thread.html
  - factory_dashboard/thread.py
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
On a signed-off card's thread, the review's sheet is folded into a closed "The review · signed off <date>", so the lead's latest answer is the first thing on a phone.

### Context
Read `#review` in `factory_dashboard/templates/thread.html` (lines 34–59) and where `factory_dashboard/thread.py` builds `review` for it. Lead ticket: its tests are in `tests/factory_dashboard/test_thread.py`. This also answers f50-F4 (a signed-off sheet carries no word that it is).
- Today the sheet sits above `#conversation`, so on a phone the latest answer is below the fold (F95's page: a screen of sheet first), against F30's "no scrolling to reach it".
- Once the card is signed off, draw `#review` as a closed `<details>` whose summary is "The review · signed off <date>", the date from `milestones.ended`. While it waits for the sign-off (ripe, or signing off), it stays open as today, with its button.

### Done when
- a signed-off card's thread: `#review` is a closed `<details>`, its summary reads "The review · signed off 2026-10-14" (that card's date), and opening it shows every section and the link to the whole review
- a ripe card's thread: the sheet is open with its Sign off button, as today
- at phone width, a signed-off card's latest lead message is above the fold
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

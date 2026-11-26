---
id: f306-01-arrows-above-the-points
milestone: f306-the-arrows-to-move-between-points
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/_partials/deck_nav.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/static/deck.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_proposal.py
---

### Goal
On a phone, the ◀ ▶ that step through a reply's points or a review's key points sit above the points and stay in place, and each point opens on a larger headline.

### Context
The picture to build is `.softfield/cards/f306-mockup/arrows-stay-put.html`, Proposed (without its green marks and notes). Read D1–D5 in `.softfield/cards/f306-the-arrows-to-move-between-points.md`. The nav is `factory_dashboard/templates/_partials/deck_nav.html`, included after the deck in `factory_dashboard/templates/thread.html` and `factory_dashboard/templates/proposal.html`; `factory_dashboard/static/deck.js` binds it as the deck's `nextElementSibling`. The phone rules are in `factory_dashboard/static/dashboard.css` under the f6-10 comment ("The planning room on a phone"); the top bar (`header.bar`) is sticky, so D3's scroll must leave the nav below it. `test_on_a_phone_one_point_shows_at_a_time` in `tests/factory_dashboard/test_thread.py` is the phone test to extend, with its review case.

### Done when
- at 390 px, on a thread and on a review, the nav (count, dots, ◀ ▶) comes before the first point, and the deck.js stepping, the commented dots and the 44 px controls work as before
- stepping through points of different lengths with ▶, the arrows' position on the screen doesn't change
- the nav reads "Point N of M" for the point shown
- with the page scrolled so the nav is under the top bar, pressing ▶ shows the nav fully below the top bar; with the nav in view, pressing ▶ doesn't scroll
- on a phone a point's title is 18 px in the display font; on a wide screen the pages look as before, with no nav
- the listed `tests:` pass, and fail without the change

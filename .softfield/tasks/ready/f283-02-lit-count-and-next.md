---
id: f283-02-lit-count-and-next
milestone: f283-the-current-planning-search-reloads-the
difficulty: 2
depends_on: [f283-01-find-lights-up]
files:
  - factory_dashboard/static/board.js
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
While the board's Find box holds text, the owner sees how many cards are lit, in all and in each stage, and can jump from one lit card to the next, on a phone too.

### Context
Read D3 in `.softfield/cards/f283-the-current-planning-search-reloads-the.md`. The picture to build is `.softfield/cards/f283-mockup/board-highlight.html`, Proposed: the "N lit" plate with Next › beside the box, and the "N lit" tag on each plot (wide and phone).
- f283-01 added the lighting in `factory_dashboard/static/board.js` (the `lit` class on `.slot`): count from it, after each change of the box and after `refresh`.
- Next › scrolls the next lit card, in the page's order, to the middle of the screen and moves the focus to its link; after the last it starts again. Under 900 px, when the next lit card is in another stage, it shows that stage first, the way pressing its plot does.
- The plots' tags show only while the box holds text, and a plot's count and ripe light stay as `refresh` keeps them. Use `--lit` from f283-01; a stage with none lit has the plain dashed tag.

### Done when
- in the browser: typing "top bar" shows "N lit" with N the number of lit cards, and each plot's tag gives its stage's share; clearing the box hides the tags
- Next › brings each lit card into view in turn, then the first again; with nothing lit it is disabled
- at 390 px wide, Next › to a lit card in another stage shows that stage
- the listed `tests:` pass, and the new ones fail without the change
- all gates pass (see `docs/workflow.md`)

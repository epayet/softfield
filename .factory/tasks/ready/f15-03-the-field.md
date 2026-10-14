---
id: f15-03-the-field
milestone: f15-reprioritising-tickets
difficulty: 5
depends_on: [f15-02-board-shows-the-order]
agent: lead
files:
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/_partials/stage_icon.html
  - factory_dashboard/static/board.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
The board opens on the field: six plots in growth order, each with its plant and its count; on a phone a tap on a plot shows that stage alone, and nothing scrolls sideways.

### Context
Read `.factory/cards/f15-reprioritising-tickets.md` (D2) and the picture, `.factory/cards/f15-mockup/board-edit.html` (Proposed: `.plots`, `.plot` and `plant()`), `factory_dashboard/templates/board.html`, `factory_dashboard/templates/_partials/stage_icon.html`, the board's rules in `factory_dashboard/static/dashboard.css`, and in `tests/factory_dashboard/test_board.py` `test_the_board_lays_out_at_phone_and_display_sizes`, `test_the_columns_scroll_sideways_on_a_narrow_desktop` and `test_the_totals_count_each_stage`.
- **The plots** replace the totals row: six buttons in growth order, three to a row under 900 px and six in a row from 900 px, each with its drawing (a seed, then a plant taller stage by stage, a fruit when ripe, a crate when harvested: our own SVG, in the theme's inks; see F88's D1 to D3), its count and its name. Ripe's count is hazard yellow when it has cards.
- **Under 900 px** one stage shows at a time: planted at first, or the stage named in the address's `#stage-…`; a tap on a plot shows its stage and marks the plot pressed (`aria-pressed`). Without script every stage shows, stacked, as today.
- **From 900 px** all six stages show side by side, and a plot scrolls to nothing: it is a count.
- New script goes in `factory_dashboard/static/board.js`, loaded by the board only, with the `?v=` the other static links carry.
- The page's body never scrolls sideways at 390 px; the test about sideways scrolling on a narrow desktop is rewritten to what this ticket draws.

### Done when
- at 390 × 844 the six plots sit three to a row inside the page's width, each at least 44 px tall, and only the planted stage's cards show
- tapping the Seed plot shows the seed stage alone and presses that plot; opening `/board#stage-ripe` shows ripe
- at 1280 px six plots are in one row and six stages side by side
- each plot's count equals the cards of its stage (harvested: all of them, not only the four shown)
- with scripts off (the page fetched by the test client) every stage is in the HTML
- at 390 px `document.documentElement.scrollWidth` is not wider than the window
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

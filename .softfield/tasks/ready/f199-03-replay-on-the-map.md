---
id: f199-03-replay-on-the-map
milestone: f199-let-s-improve-the-factory-floor
agent: lead
difficulty: 6
depends_on: [f199-01-the-map, f199-02-strip]
files:
  - factory_dashboard/line.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/floor.html
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/_partials/away.html
  - factory_dashboard/templates/_partials/line.html
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
Replay lives on the map, and the old floor drawings are gone from the Overview and from the code. While you were away keeps its own choice of stretch.

### Context
Decision D7 in `.softfield/cards/f199-let-s-improve-the-factory-floor.md`; the picture is `.softfield/cards/f199-mockup/floor.html`.
- The replay bar and its `choices` are in `factory_dashboard/templates/overview.html` and `overview` in `factory_dashboard/overview.py`. `#replay-span`'s handler in `factory_dashboard/static/factory.js` also swaps the Away panel (f9-14): that part stays on the Overview, with a select of its own at the head of `factory_dashboard/templates/_partials/away.html`. The replay's part goes to `factory_dashboard/templates/floor.html`, which needs the page's `data-replay` too.
- The `line_seen` cookie (`SEEN` in `factory_dashboard/line.py`) keeps meaning "when the owner last opened the line": check where it is set, so that opening the Overview or the map both count as today.
- Delete from `factory_dashboard/static/factory.js`: `draw`, `drawPhone`, `BELTS`, `PHONE_BELTS`, `AREAS`, `PHONE_AREAS`, `QUEUE`, `PHONE_QUEUE`, and the functions only they use; from `factory_dashboard/static/dashboard.css` the rules only they use. `.floor-wrap` and `svg#floor-phone` go.
- `factory_dashboard/templates/_partials/line.html` holds only the map's parts now; `/line/live` still renders it. `/line` keeps its redirect to `/`.
- `factory_dashboard/templates/board.html`'s "Planted cards feed the factory floor" links to `/floor`.
- `tests/factory_dashboard/test_line.py`: a test of a behaviour that remains (replay, crate card, seeds card, clog, checks light, belts' document) moves to the map; a test only of the old drawing's geometry goes. Say in the commit how many went, and why.

### Done when
- the Overview has the strip, no floor drawing and no replay bar; While you were away still changes its stretch in place, with its address updated
- on `/floor`, Replay plays any stretch, step by step, as it does today; "Back to live" draws the live document
- a phone's replay controls are at least 44 px and don't push the map off screen: the page may scroll only while a replay's controls show
- a tap on a crate still opens the crate's card, on the map, in a replay too
- `factory.js` holds one set of coordinates, the two tables of f199-01
- the board's link goes to `/floor`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f5-16-board-page
milestone: f5-board
depends_on: [f5-14-factory-look, f5-15-board-data]
agent: lead
difficulty: 5
files:
  - factory_dashboard/board.py
  - factory_dashboard/app.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
`/board` shows the field: six columns of cards from seed to harvested, with totals, search and a kind filter, laid out as the mock-up shows on desktop and phone.

### Context
Read the board mock-up (`docs/milestones/f5-board-mockup/Main.dc.html`, `docs/milestones/f5-board-mockup/Phone.dc.html`, `docs/milestones/f5-board-mockup/Card.dc.html`: read the markup and the data in each file's script, not a page to open), `factory_dashboard/board.py` (`board`, from f5-15), `factory_dashboard/overview.py` (the route and template pattern), `factory_dashboard/app.py` (`create_app` includes each page's router), `factory_dashboard/templates/base.html` and the tokens in `factory_dashboard/static/dashboard.css` (f5-14).
- **Read-only** (ADR 19 item 4). The search and the kind filter are a plain GET form (`?q=`, `?kind=`): no script.
- **Desktop:** the totals strip, then six columns, each headed by its stage's icon (inline SVG, as in the mock-up) and count, then the cards. The columns scroll sideways below about 1240 px.
  - **Cards:** an edge in the area's colour; a bug's edge is striped and its label says "bug".
  - "Growing cards feed the factory floor ›" links to `/`.
- **Phone (under 640 px):** stacked sections in the mock-up's order: ripe, growing, planted and sprouting, seeds, harvested (what's running and what needs the owner first: the owner, 2026-10-03). Every tap target is at least 44 px.
- **Colours:** the mock-up's `#hex` values are a picture; the page uses the tokens (`test_templates_use_the_tokens_never_raw_colours` in `tests/factory_dashboard/test_app.py` fails a raw colour in a template).
- A milestone card links to `/milestones/<full key>` (the route's key is `milestones.key`), a bug card to `/tickets/<id>`.
- Add "Board" to the top bar's tabs in `factory_dashboard/templates/base.html`, right after Planning (the owner, 2026-10-06: Overview, Planning, Board, …; a comment there marks the place). The Milestones tab stays until f5-17's card page carries a milestone's details; f5-17 removes it.

### Done when
- `/board` lists each card in its stage's column, asserted within that column
- `?q=` and `?kind=bug` narrow the cards
- the harvested column shows 4 cards and "2 more harvested" when there are 6
- a bug card shows "bug" and links to its ticket page
- the top bar has a Board tab right after Planning, current on `/board`
- the layout check passes at phone and desktop sizes (`layout_problems` in `tests/browser/conftest.py`, as `tests/factory_dashboard/test_planning.py` uses it)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

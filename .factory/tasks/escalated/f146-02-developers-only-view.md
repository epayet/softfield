---
id: f146-02-developers-only-view
milestone: f146-some-kind-of-view-or-toggle
difficulty: 3
depends_on: [f146-01-developer-line]
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
The board has a "developer's view" lever: turned on, the same board lights the cards developers can work on, half-darkens those whose developer work waits for the lead and fades the lead-only ones, each card saying so in words, with drag and Send new order working as usual.

### Context
Read `.factory/cards/f146-some-kind-of-view-or-toggle.md` (D3–D5) and build the Proposed board of `.factory/cards/f146-mockup/developers-only.html`; its Today is the live page.
- `factory_dashboard/board.py`: `board_page` takes `kind` and `q`; add `view` the same way (`developers` turns it on, anything else is the normal board) and call `board(..., developers=True)` (f146-01) in that view.
- The lever is a link, not a form button: it goes to `/board` with `view=developers` (or without it), keeping `q`, `kind` and `?project=`. It looks like the allowance panel's `.lever` (`factory_dashboard/templates/_partials/allowance.html`). The search form keeps `view` in a hidden input, as it keeps the project.
- `factory_dashboard/templates/board.html`: the `card_link` macro and its `.slot` get the look as a class (`dev-can`, `dev-waits`, `dev-none`) and the card's line from `DevWork`, worded as the mock-up; the Planted stage head gets the totals line; the field a one-line legend. Nothing else in the page changes: the plots, every stage, the grips, ⋯, `#board-line` and the order bar stay as they are.
- New CSS uses the tokens at the top of `dashboard.css` only; the developer colour is `--dev` and the lead's `--opus`, as on the floor's legend. A faded card still shows its words and comes back on hover or focus.

### Done when
- `/board` shows the lever after the kinds, off; `/board?view=developers` shows it on
- in the view, a planted card developers can work on reads "developers: 1 now · 5 after it" with what follows it, a waiting one names the lead tickets, a lead-only one says "lead only"
- the Planted stage head says how many cards and tickets developers can work on, and for about how long
- searching or picking a kind keeps the view; the lever off gives the normal board, unchanged
- dragging a card in the view and pressing Send new order posts the same reorder as from the normal board
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 725004
logs: .factory/var/runs/20261029-143524/f146-02-developers-only-view
```

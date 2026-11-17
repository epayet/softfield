---
id: f133-03-board-without-areas
milestone: f133-each-project-has-its-own-series
agent: developer
difficulty: 3
depends_on: [f222-03-pages-read-the-order]
files:
  - factory_dashboard/board.py
  - factory_dashboard/thread.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
The board, a card's page and a thread's title stop showing factory or product: every card has the same yellow edge, the kind filter is All and Bugs, and the legend no longer explains areas.

### Context
The picture to build: `.softfield/cards/f133-mockup/board.html` (Proposed). Read D5 in `.softfield/cards/f133-each-project-has-its-own-series.md`, then `KINDS`, the `kinds` list, the `area` field and where it is set in `factory_dashboard/board.py`, the `card_link` macro and the legend in `factory_dashboard/templates/board.html`, the `card-head` header and its Area row in `factory_dashboard/templates/milestone.html`, `_header` in `factory_dashboard/thread.py`, and the `.card.factory`, `.card.product`, `#card-head.factory`, `#card-head.product` and `.swatch.factory`, `.swatch.product` rules in `factory_dashboard/static/dashboard.css`.
- F222's ticket f222-03 changes the same card page and board first (the place in place of the priority): keep what it did.
- A card's edge colour, and a card page's header edge, is `var(--factory)` for every card that is not a bug; a bug keeps its stripes. The `--factory` and `--product` tokens stay (`--product` colours the Planted stage); their comment stops calling them the board's areas.
- The card's small line shows its place and key, and "bug" on a bug, nothing else. The "growing" tag, the "working now" legend entries and the developer's view lever stay as they are.
- `kind=factory` or `kind=product` in an old link shows every card, as an unknown kind does today.
- Leave the review's idea plates in `factory_dashboard/milestones.py` alone: their factory/product is where an idea is planted.
- Update the template and CSS comments that say "its area's colour".

### Done when
- the board's HTML has no `factory` or `product` word on a card, no Factory or Product filter button, and no "product (for Mum)" in the legend
- a non-bug card's edge is the same yellow whatever its database row's `area`; a bug's is striped and its line says "bug" alone
- the card page has no Area row, and a thread's title has its status beside it and never its area
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 5391
gate_failures: ['stopped', 'stopped']
tokens: 4329881
```

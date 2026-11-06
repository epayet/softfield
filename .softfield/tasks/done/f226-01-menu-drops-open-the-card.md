---
id: f226-01-menu-drops-open-the-card
milestone: f226-the-open-card-s-from-the
difficulty: 1
depends_on: []
files:
  - factory_dashboard/templates/board.html
  - tests/factory_dashboard/test_board.py
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
The ⋯ menu of a card on the board no longer offers "Open the card", since tapping the card goes to the same page. A card with nothing else to offer shows its moves and Close alone.

### Context
The picture to build is `.softfield/cards/f226-mockup/menu.html` (Proposed).
- In `factory_dashboard/templates/board.html`, the macro `card_actions` writes each card's `template.card-actions`, which `factory_dashboard/static/board.js` copies into the menu. Remove its "Open the card" link.
- Write no template at all when the card has no `c.thread`: an empty one would copy its white space into `.order-actions`, which the `:empty` rule in `factory_dashboard/static/dashboard.css` then doesn't hide. The script already handles a slot with no template. Leave the script and the CSS as they are.
- The whole card stays a link to `card_href(c)`; that macro is still used by `card_link`.
- In `tests/factory_dashboard/test_board.py`, the tests that name "Open the card" follow: `test_each_placed_card_s_actions_lead_to_its_conversation_set_aside_and_its_page` (rename it, it no longer leads to the card's page; its loop over the stages now checks no card's actions hold that link, and that the card's own link still goes to the card's page) and `test_the_menu_shows_a_card_s_actions_under_its_moves_and_sets_it_aside`. The helper `_actions` already returns None for a slot with no template.

### Done when
- at 390 px on `/board`, the ⋯ of a card with a conversation shows Top, Up, Down, Bottom, Open its conversation, Set aside and Close on a seed or a sprouting card, and the same without Set aside on a planted card
- the ⋯ of a bug or of a card with no conversation shows Top, Up, Down, Bottom and Close, and `.order-actions` takes no height, also straight after opening another card's menu that had actions
- tapping a card still opens its page
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1534
gate_failures: []
tokens: 927829
```

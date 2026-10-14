---
id: f110-02-ripe-card-leads-to-sign-off
milestone: f110-i-don-t-understand-why-there
depends_on: [f110-01-ripe-is-one-rule]
difficulty: 3
files:
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
A ripe card on the board says where to sign off in plain words and opens its page at the Sign off button, in place of a terminal command.

### Context
Read `factory_dashboard/templates/board.html` (the `card_link` macro), `factory_dashboard/templates/milestone.html` (the `#review` section, where the button is) and `.factory/cards/f110-i-don-t-understand-why-there.md` (D2). Follow the tests about a card's words in `tests/factory_dashboard/test_board.py`.
- A ripe milestone's card ends with `uv run runner signoff <key>` in a `code` element today. Replace it with the words "Read the review and sign off ›", styled as the card's other small lines.
- The whole card is one link: a ripe milestone's goes to its page at `#review` (the fragment after the `?project=` part). Every other card's link stays as it is.
- No button on the board: the sign-off stays beside the review (D2). The page stays read-only, with no script.

### Done when
- a ripe milestone's card shows "Read the review and sign off" and no `uv run runner signoff`
- its link ends with `#review`, after the project's query
- a growing card's and a harvested card's links have no fragment, and neither shows the words
- on a phone, the ripe card's words fit inside the card
- the listed tests pass, and fail without the change

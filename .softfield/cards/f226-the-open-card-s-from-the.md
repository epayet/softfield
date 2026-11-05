# Milestone F226: Remove 'Open the card' from the board's ⋯ menu

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-05.

## Notes
The 'open card's from the board 3 dots button is not useful

## Plan
Mock-up: [`f226-mockup/menu.html`](f226-mockup/menu.html).
- **D1 "Open the card" leaves the ⋯ menu.** It goes to the same address as tapping the card (one `card_href` in `factory_dashboard/templates/board.html`, and a test holds them equal). This replaces that one action of F15, Reprioritising tickets, D7. The moves, Open its conversation and Set aside stay as they are, on the same cards.
- **D2 A card with no conversation has no actions, and no template.** A bug, or a card with no thread, gets no `card-actions` template, so its menu is the moves and Close. An empty template would still copy its white space into `.order-actions`, which `:empty` doesn't hide, and leave a gap.
- **D3 What doesn't change:** the ⋯ stays on every placed card, for its moves; the ripe card's own link to its review; the card's tap.

| # | Ticket | Who | Difficulty | Waits for | What |
|---|---|---|---|---|---|
| 01 | menu-drops-open-the-card | developer | 1 | – | D1 and D2 in the template; the tests follow |

## Before and after
`/board` shows the ⋯ menu only once it is pressed, so its pictures show the page, not the menu: read the menu from the mock-up, or press ⋯ to check it.
- `/board`

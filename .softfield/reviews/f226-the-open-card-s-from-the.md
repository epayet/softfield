# Review: F226, the ⋯ menu no longer offers "Open the card"

## Sign-off sheet

### 1. What changed
On the board, a card's ⋯ menu no longer has an "Open the card" button. Tapping the card itself already opened the same page.
- A card with a conversation still offers "Open its conversation". On a seed or sprouting card it also offers "Set aside".
- A bug, or a card with no conversation, now shows only the four moves and Close. There's no empty row under the moves.

The after pictures show the board as it loads. The menu only appears when you tap ⋯, so the pictures look the same as before and can't be compared with the mock-up. The browser test checks the menu's contents for the three cases in the mock-up. Judged by the code and that test, it matches the mock-up.

### 2. How to test it yourself
1. On the phone, open the Board and tap ⋯ on a sprouting card that has a conversation. You should see Top, Up, Down, Bottom, "Open its conversation", "Set aside" and Close. There should be no "Open the card".
2. Tap ⋯ on a planted card. You should see the same, without "Set aside".
3. Tap ⋯ on a bug. You should see the four moves and Close, with no gap between them.
4. Close the menu and tap the card itself. Its page should open.

### 3. Left for later
Nothing set aside. There are two small notes and neither is worth a run (see Findings).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-05: Claude (Opus) planned the card and drew the mock-up in 2 minutes ($0.92).
- 2026-11-06: the local model (Qwen) did the one ticket on its first attempt in 26 minutes. Nothing was escalated.
- Lessons:
  - The ticket named a trap: an empty `<template>` would copy its white space into the menu and leave an empty row. The model avoided it as told. When a ticket names that kind of detail, a small UI ticket passes on the first attempt.
  - Nothing new needs changing.
- Logs: `.softfield/sessions/` (the 2026-11-06 run).

### 6. What next
- **Product:** product work is still on hold, as you asked.
- **Factory:** the before and after pictures only show a page as it loads. A change inside a menu or dialog can't be seen in them. If more cards change menus, the shots could take an optional "open this first" step for each page. That's not worth doing for one card, so I'm only noting it here.

### 7. What clogged the factory line
Taken from the `jobs` table:
- **Waiting for this review: about 5½ days** (11-06 17:57 to 11-12 03:42). The ticket was merged and waited in the queue for its review while other work went first. No agent sat idle because of it.
- No failed attempts, no limits hit and no stops for you.

<!-- runner report -->
<!-- /runner report -->

## What was built
`f226-01-menu-drops-open-the-card` (commit c5d647005):
- **Template:** in `factory_dashboard/templates/board.html`, the `card_actions` macro drops the "Open the card" link. It now writes no `<template>` at all when a card has no conversation. `board.js` already handles a card with no template: `replaceChildren()` with nothing leaves `.order-actions` truly empty, and the `:empty` rule hides it. As the ticket asked, the script and the CSS are untouched. `card_href` is still used by the card's own link.
- **Tests:** two existing tests in `tests/factory_dashboard/test_board.py` were edited, both as the ticket listed:
  - `test_each_placed_card_s_actions_…` is renamed. It now expects no template on bugs and on cards without a conversation, and it checks that no placed card offers "Open the card". The check on the card's own link now only asserts that the link exists. Its address is still checked by other tests (`_links` near line 1123 and line 1197).
  - The browser test on the menu drops "open the card" from the sprouting card's list. It expects an empty list for F20, which it opens straight after F21's menu, so leftovers from the previous menu would show.

All 149 board tests pass. There is no French in this milestone.

## Findings
| Id | Grade | Route | What |
|---|---|---|---|
| F1 | nit | report | The after pictures show `/board` as it loads, not the open ⋯ menu, so they can't show this change. See "What next" for a possible fix. |
| F2 | nit | report | The browser test checks that F20's menu has no children, not that `.order-actions` takes no height, which is what Done when said. With no children, `:empty` hides the row, so the behaviour is right. The test just states it less directly. |

**No checkpoint findings.** None were raised.

**Score: 9/10.** The change is small and correct, follows the ticket and mock-up exactly, and passed on the first local attempt. The tests were adjusted only where the ticket said to.

## Set aside
Nothing.

## Workflow observations
- This is a good example of a local-sized ticket: one template macro, two named tests, and the one trap spelled out. It cost no Claude time beyond planning and this review.
- The pictures step ran but couldn't show a change behind a tap (F1). This is fine for now. If it happens again, it's worth a ticket.

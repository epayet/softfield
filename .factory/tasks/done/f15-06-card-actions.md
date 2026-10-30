---
id: f15-06-card-actions
milestone: f15-reprioritising-tickets
difficulty: 4
depends_on: [f15-05-replan, f73-02-set-aside-button]
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/board.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
A card's ⋯ menu on the board also leads to what the owner does with that card: its conversation, setting it aside, and its own page.

### Context
Read `.factory/cards/f15-reprioritising-tickets.md` (D7 and the Replan) and the picture, `.factory/cards/f15-mockup/board-edit.html` (its `sheet` function's buttons).
- **What is there today:** one `<dialog id="order-sheet">` at the foot of `factory_dashboard/templates/board.html`, holding the move row (`.order-moves`, buttons `data-move="top"`…) and Close. `factory_dashboard/static/board.js` gives each `.slot` of a stage in `PLACED` (seed to growing) a `.more` button (`aria-label` "Move F27") in `setUp`, whose click fills the sheet's `h3`, sets `menuFor` and calls `sheet.showModal()`. Ripe and harvested cards have no ⋯, and stay so: a ripe card's own link already ends in `#review` and says "Read the review and sign off ›" (f110).
- **Where the facts are:** `_cards` in `factory_dashboard/board.py` builds each `Card`; its `threads` set holds the short keys (`f15`) of the threads not archived, plus those with an owner's message on its way. A thread's page is `/planning/<short key>` (`factory_dashboard/thread.py`, `@router.get("/planning/{thread}")`). The card's own link is the one `card_link` in `board.html` builds today.
- **The set-aside request:** kind `archive`, subject the thread, value `on`, as `#archive-button` in `factory_dashboard/templates/thread.html` posts it (f73-02's `#set-aside-button` posts the same). An open one is found as `factory_dashboard/thread.py` finds it (`kind = 'archive'` and `done IS NULL` in `owner_requests`).

What to build:
- `Card` gets `thread: str` (the short key, lower case, of a milestone whose key is in `threads`; `""` for a bug or a card with none) and `setting_aside: bool` (an open `archive` request with value `on` for that thread).
- Each placed slot carries its own actions, rendered by the server in a `<template class="card-actions">` inside the `.slot`, each link keeping the page's project query (`q`) and at least 44 px tall:
  - "Open its conversation" to `/planning/<thread>`, when the card has a thread;
  - "Set aside", a `<button type="button" class="set-aside" data-thread="<thread>">`, on a seed or sprouting card with a thread; when `setting_aside`, it is disabled and reads "Set aside · on its way";
  - "Open the card", to the card's own link.
- `#order-sheet` gets a `<div class="order-actions">` under `.order-moves`. On a ⋯ press, board.js fills it with a copy of that slot's template. "Set aside" posts the request with the same `fetch("/requests", …)` call shape as the send (`HX-Request` header, `URLSearchParams` with `kind`, `project`, `subject`, `value`); while it posts and after, the button is disabled and reads "Set aside · on its way"; if the post fails it says so and is pressable again.
- The ⋯ `aria-label` becomes "Actions for F27" (the mock-up's); `test_the_menu_does_the_same_moves_by_keyboard_too` follows. `test_the_page_posts_only_a_reorder_and_links_to_the_factory_floor` now allows `archive` beside `reorder`, and still no `hx-post`.
- Planting is not on the board: it stays on the planning desk (D7).

### Done when
- a sprouting card's slot has "Open its conversation" to `/planning/<its key>?project=…` and a "Set aside" button with `data-thread` its key
- a seed with no thread has neither; a bug's has no conversation link and no Set aside; a planted or growing card has no Set aside
- every placed card's actions have "Open the card" with the card's own link
- a card whose `archive` request is open shows "Set aside · on its way", disabled
- in Chromium, at 390 px: ⋯ on a sprouting card shows the moves, then the three actions; pressing "Set aside" posts one request (kind `archive`, the thread, `on`) and the button is disabled
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 221255
logs: .factory/var/runs/20261029-222125/f15-06-card-actions
```

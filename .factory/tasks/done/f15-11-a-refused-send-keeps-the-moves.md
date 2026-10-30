---
id: f15-11-a-refused-send-keeps-the-moves
milestone: f15-reprioritising-tickets
difficulty: 3
depends_on: []
files:
  - tests/factory_dashboard/test_board.py
tests:
  - tests/factory_dashboard/test_board.py
finding: f15-reprioritising-tickets-F2
tests_only: true
---

### Goal
Test what the board does when the dashboard refuses a send or a Set aside: the owner's moves are kept and they can press again.

### Context
The code is right; nothing tests its failure branches. In `factory_dashboard/static/board.js`:
- the "Send new order" click, when `fetch("/requests", …)` fails or answers not ok, re-enables the button, writes "Not sent: the dashboard didn't take it. Your moves are kept; try again." in the bar's `p`, and keeps the moved cards where they are, still marked;
- the "Set aside" click in the ⋯ sheet (`.order-actions`), on the same failure, reads "Set aside · not sent, try again" and is pressable again.

Worked examples in `tests/factory_dashboard/test_board.py`: `test_send_posts_the_whole_open_order_once_and_the_board_shows_it_on_its_way` (drag, then send) and `test_the_menu_shows_a_card_s_actions_under_its_moves_and_sets_it_aside` (the sheet's Set aside). Make the post fail with `page.route("**/requests", lambda route: route.fulfill(status=500))`, as `tests/factory_dashboard/test_thread.py` does with a 400. Use the helpers already there (`_three_planted`, `_drag`, `_bar`, `_words`, `_order`).

### Done when
- a send the dashboard answers with 500: the bar stays, its words are "Not sent: the dashboard didn't take it. Your moves are kept; try again.", "Send new order" is enabled, the planted order is the moved one, and the moved card still says "moved · was #4 · not sent yet"; no `reorder` row is in `owner_requests`
- after `page.unroute("**/requests")`, a second press sends one `reorder` and the card shows "on its way"
- a Set aside the dashboard answers with 500: the button reads "Set aside · not sent, try again" and is enabled; no `archive` row is in `owner_requests`
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 217043
logs: .factory/var/runs/20261030-015512/f15-11-a-refused-send-keeps-the-moves
```

```yaml
# --- runner ---
result: done
finished_by: lead
```

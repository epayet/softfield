---
id: f192-03-fix-back-redraw-stage-and-tests
milestone: f192
difficulty: 4
depends_on: []
files:
  - tests/factory_dashboard/test_board.py
tests:
  - tests/factory_dashboard/test_board.py
finding: f192-02-board-back-redraws
tests_only: true
---

### Goal
Prove in tests that the board's back-button redraw (`pageshow` with `persisted`) puts each card in its own stage and order as the server holds them now, and make one test's name match what it checks.

### Context
The code is right: change only tests. They pass on main's code, as they should. In `factory_dashboard/static/board.js`, the `pageshow` handler calls `refresh`, which swaps in the fresh page's `.stages` and `board-line` and calls `setUp`; `setUp` builds its stage map by key from the fresh `board-line`. The checkpoint's finding described an index lookup that is not in the code.

What is missing is in `tests/factory_dashboard/test_board.py`:
- `test_pageshow_with_persisted_true_draws_the_field_with_grip_and_menu` already changes the database after the page opened and waits for the plate, but no card changes place or stage in it, so nothing there would catch a card given another card's stage.
- `test_pageshow_with_moved_card_fetches_and_keeps_moves` says "fetches" in its name, while its docstring and assertions say nothing is fetched.

Facts for the new tests, all from that file and `tests/factory_dashboard/conftest.py`:
- `_three_planted` opens the board on a phone with the planted order `["f24", "f23", "bug-02-stale", "f27", *STARTED]`.
- A `_reorder` request whose value is the whole line, as JSON, with `f27` before `f23`, makes the planted order `["f24", "f27", "f23", "bug-02-stale", *STARTED]`, and F27's card carries `.card.on-its-way` (`_order` reads it; `test_sending_from_the_view_posts_the_same_reorder` waits on that same locator).
- F20 (`f20-duck-pond`) starts as a seed: `_order(page, "seed")` is `["f20", "bug-01-duck-count"]`. `_planted(("f20-duck-pond", 9))` sets its state to ready, which makes it planted.

### Done when
- The test `test_pageshow_with_unsent_moves_keeps_order_and_skips_fetch` replaces `test_pageshow_with_moved_card_fetches_and_keeps_moves`, with a docstring saying no board request is made and the order stays. Its assertions stay as they are.
- A new test: after `_three_planted`, write the `_reorder` above, fire `pageshow` with `persisted: true`, and wait for `.slot[data-key=f27] .card.on-its-way`. It asserts the planted order is exactly the new one, the seed and sprouting orders are the same as before the redraw, and no card has `.moved`.
- A new test: after `_three_planted`, write the `_planted` for F20 above, fire `pageshow` with `persisted: true`, and wait for F20's slot in `#stage-planted`. It asserts F20's slot has `data-stage` "planted", `f20` is in `_order(page, "planted")`, `_order(page, "seed")` is exactly `["bug-01-duck-count"]`, and F20's slot has exactly one `.grip`.
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 3628572
logs: .softfield/var/runs/20261105-024727/f192-03-fix-back-redraw-stage-and-tests
```

```yaml
# --- runner ---
result: done
finished_by: lead
```

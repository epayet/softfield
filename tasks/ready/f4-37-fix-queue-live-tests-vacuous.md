---
id: f4-37-fix-queue-live-tests-vacuous
milestone: f4-always-on
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
- factory_dashboard/templates/_partials/queue.html
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C17-1
---

### Goal
Fix a checkpoint finding on f4-30-queue-live-tests: its new and rewritten tests in `tests/factory_dashboard/test_overview.py` pass without proving what the ticket asked, and it dropped checks that were already there.

### Context
Read `tasks/done/f4-30-queue-live-tests.md` and its merge (`git show ee5522fa49dc78cb6b62f952ad1905e468eb8786`). Facts, in `tests/factory_dashboard/test_overview.py`:
- `test_live_queue_matches_root` compares two id lists that are both empty if the Queue rows vanish from either page; it never asserts the list is non-empty or holds `f1-05-first` before `f1-06-second`. It also splits on the first "Next in line", not on the `queue` section.
- `test_running_and_queue_share_a_row_on_root` uses `<div class="row">.*id="now".*id="queue"` with `re.S`: greedy, it matches when the two sit in different `.row` divs. The ticket asked for "inside one `.row`".
- `test_live_queue_updates_between_polls` reads the count with `re.search(r"(\d+) ticket", ...)` on the whole `/live` page, not on the queue section, and never checks that `f1-99-new` shows up.
- `test_the_live_partial_answers_on_its_own_for_htmx` now repeats its first four assertions twice, and lost `assert "hx-get" not in html` (the partial is bare) and `assert client.get("/running").status_code == 404`.
- `test_the_overview_shows_every_panel_in_order` lost `'id="running"' not in html and 'id="queue"' not in live`-style checks for the old ids; `'id="now"' in html` is a presence check with a comment that says nothing.
- `test_another_project_shows_only_its_own` asserts `"Now refreshes" in now`, a string unrelated to this change.
- `test_now_holds_what_works_...` ends with `"uv run runner run" not in next_in_line`, which is true only because the drain line sits before "Next in line" in the queue partial; it checks nothing about the Queue.
- `factory_dashboard/templates/_partials/queue.html` prints "The queue is empty." twice when nothing waits (once in the panel, once under "Next in line").

### Done when
- `/live` and `/` give the same non-empty Queue rows in the same order, read from the `queue` section, with `f1-05-first` before `f1-06-second`
- the update test reads the count from the `queue` section and sees `f1-99-new` and its title in the second `/live` answer
- the row test fails when the Queue section is in another `.row` than `now` (match inside one `.row` div, not across the page)
- the duplicated assertions are gone; the bare-partial check (no `hx-get` in `/live`) and the `/running` 404 are back
- the "Now refreshes" assertion and the meaningless drain-command negation are replaced by a check that matters (the drain command is in the queue section and not in the now section) or removed
- an empty queue shows "The queue is empty." once
- the listed `tests:` pass, and each new or changed test fails if the Queue is taken out of `_partials/live.html`
- all gates pass

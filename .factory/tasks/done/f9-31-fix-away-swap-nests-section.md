---
id: f9-31-fix-away-swap-nests-section
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- factory_dashboard/static/factory.js
- factory_dashboard/templates/_partials/away.html
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f9-line-polish-C5-1
---

### Goal
Fix a checkpoint finding on f9-14-away-span-in-place: choosing another stretch puts a whole "While you were away" panel inside the old one, and the tests would not notice.

### Context
Found by the lead at a checkpoint, on the merge of `tasks/done/f9-14-away-span-in-place.md`. Read the `#replay-span` handler in `factory_dashboard/static/factory.js`, `factory_dashboard/templates/_partials/away.html` and the two f9-14 tests in `tests/factory_dashboard/test_overview.py`.
- `/away` returns `factory_dashboard/templates/_partials/away.html`, whose root is `<section id="away" class="panel">`; the handler sets `document.getElementById("away").innerHTML` to it. So after one choice the page holds `#away` inside `#away` (two panels, a duplicate id); after a second choice `getElementById` still finds the outer one and nests again.
- `test_choosing_a_span_updates_away_in_place` only asserts `"since" in away_text.lower()`, which the heading's "While you were away" … "since" satisfies before and after the change; it never compares the time shown with the old one nor counts `#away` elements.
- `test_replay_asks_new_since_after_span_change` reads `dataset.replay` only; nothing clicks Replay and checks the `/line/replay` request carries the new `since`.
- The comment at the top of `away.html` still says "at page load only".

### Done when
- after choosing "the last hour", the page has exactly one element with id `away`, and its "since HH:MM" text is the new time (and differs from the one before)
- after the choice, starting the replay requests `/line/replay` with the new `since`
- the tests for it fail on main
- the listed `tests:` pass
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 6387
gate_failures: ['task-tests', 'task-tests']
tokens: 1868380
```

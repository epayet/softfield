---
id: f8-12-fix-queue-view-tests-do
milestone: f8-one-queue
difficulty: 4
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f9-line-polish-C467-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f8-07-queue-view's tests: Queue-view tests do not verify key row content and ordering in the rendered page.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f8-07-queue-view.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f9-line-polish-C467-2, should-fix: in `tests/factory_dashboard/test_overview.py`, line 1179.

### Finding
f9-line-polish-C467-2: Queue-view tests do not verify key row content and ordering in the rendered page.
> `test_queued_checkpoint_comes_before_tickets_and_shows_reason` checks for the checkpoint and reason somewhere in the section and counts ticket rows, but never checks that the checkpoint row precedes them or that its reason is within that row. `test_future_not_before_says_waits_until` does not check the displayed time. `test_done_row_isnt_shown` checks only the helper result, not that the row is absent from rendered HTML. Assert these outcomes in the page content.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1852
gate_failures: []
tokens: 1440543
```

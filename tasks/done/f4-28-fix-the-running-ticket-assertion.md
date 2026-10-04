---
id: f4-28-fix-the-running-ticket-assertion
milestone: f4-always-on
difficulty: 4
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C231-4
---

### Goal
Fix a checkpoint finding on f4-08-queue-waits-for: The running-ticket assertion can pass when the forbidden row is present

### Context
A should-fix finding (f4-always-on-C231-4) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-08-queue-waits-for.md`. What it found is under Finding.

The finding's line number (373) and the code it describes are stale. The f4-08 tests that searched the old `queue` section's text are gone. The queue tests in `tests/factory_dashboard/test_overview.py` (from `def waits(` on) now read `queue()`'s data through the `waits(db_path)` helper, keyed by ticket id. Those tests already avoid the three problems the finding names: the running ticket is checked by key, each `waits_for` is checked on its own ticket, and the ordering test asserts with no skip. Leave them as they are.

One check still reads the page loosely: `test_next_in_line_is_the_first_three_of_the_run_order`. It checks that the rows after "Next in line" in the `now` section are numbered 1, 2 and 3. It never checks which tickets those rows are, so the running ticket `f1-04-live` could be listed there and the test would still pass. Those rows come from `factory_dashboard/templates/_partials/running.html` (read it, don't change it). Each row is a number followed by a ticket link, and a row never shows a "waits for" text. So `f1-04-live` can't appear in them legitimately.

### Finding
> The condition allows f1-04-live to appear whenever “waits for f1-04-live” occurs anywhere in the queue. That dependency text is expected from another row, so this assertion can pass even if the running ticket is incorrectly listed. The other queue checks also search section-wide text rather than the target row, and the ordering test skips its assertion if either group is absent.

### Done when
- `test_next_in_line_is_the_first_three_of_the_run_order` asserts that the three ticket ids in the next-in-line rows are exactly the first three ids of `waits(db_path)`, in that order. It also asserts that `f1-04-live` is not among them. The test takes the `db_path` fixture alongside `queue_client`.
- only `tests/factory_dashboard/test_overview.py` changes
- the listed `tests:` pass
- all gates pass

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: tests-fail-on-main)
attempts: 3
tokens: 765022
logs: var/runs/20261003-233946/f4-28-fix-the-running-ticket-assertion
```

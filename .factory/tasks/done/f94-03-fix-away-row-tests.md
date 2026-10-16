---
id: f94-03-fix-away-row-tests
milestone: f94-opus-f9-25-seeds-and-planting
difficulty: 2
tests_only: true
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f94-opus-f9-25-seeds-and-planting-C2-1
---

### Goal
Fix a checkpoint finding on f94-01-away-row-facts: two away-row tests still check less than the ticket's "Done when" says.

### Context
The milestone's review (commit 53734b0, findings F1, F4, F5) already fixed most of this finding on main. These are already done, so don't change them: both "Opus" tests count "Opus" once in their own row; the no-`merged_by` test uses `away_row`, finishes its one job once and checks there is no `class="agent"`; the different-day test starts its developer job (09:00) before the escalation (11:00).

What is left, both in `tests/factory_dashboard/test_overview.py`, and nothing else:
- `test_title_text_inside_title_only` (near line 1808) checks only the row of `away-b`. `write_away` (near line 1111) gives every ticket the title `f"The {name} title."`, and the panel's rows are the tickets merged in the span: `away-a` and `away-b`. Check both rows, each with `away_row(html, <ticket>)`: the text of its `<span class="title">` equals that ticket's title, and the title is not inside that row's `<span class="how">`.
- `test_no_merged_by_shows_no_name_no_label_but_finished_and_took` (near line 1747) checks the `how` text starts with "finished " and ends with " · took 10 min", but not the time. Its job ended at 08:10 UTC, and the page prints local time, so build the expected time the way `test_finished_shows_day_when_different_day` does (`datetime(...).astimezone()`, then `%H:%M`) and assert the `how` text is exactly "finished <that time> · took 10 min". Also assert that neither `OPUS`'s display name "Opus" nor "developer attempt" appears in the row's text (`row_text`).

The template is `factory_dashboard/templates/_partials/away.html`; read it for the markup, but don't change it. Main already behaves, so these tests pass on main; that's expected (`tests_only: true`).

### Done when
- the title test asserts, on the rows of `away-a` and `away-b` separately, that the `class="title"` text equals "The away-a title." / "The away-b title." and that the title is not in that row's `class="how"` text
- the no-`merged_by` test asserts the `class="how"` text equals "finished " + the local time of 08:10 UTC + " · took 10 min", and that "Opus" and "developer attempt" are absent from the row
- no other test changes
- only `tests/factory_dashboard/test_overview.py` changes
- the listed `tests:` pass
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 4435
gate_failures: ['stopped', 'stopped']
tokens: 307449
```

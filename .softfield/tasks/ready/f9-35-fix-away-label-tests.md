---
id: f9-35-fix-away-label-tests
milestone: f9-line-polish
difficulty: 2
depends_on: []
files:
  - tests/factory_dashboard/test_overview.py
tests:
  - tests/factory_dashboard/test_overview.py
finding: f9-line-polish-F2
tests_only: true
---

### Goal
The While you were away tests prove two labels: a ticket with no `merged_by` shows no label, and Claude finishing a developer ticket whose one developer attempt passed reads "1st try".

### Context
Read `_label` in `factory_dashboard/queries.py` (the label a row of While you were away carries), and in `tests/factory_dashboard/test_overview.py` the tests `test_away_no_merged_by_shows_no_label` and `test_away_developer_ticket_merged_by_opus_after_3_jobs` (build the second test like it, with `row_text` and `away_row`).
- `test_away_no_merged_by_shows_no_label` only checks that a ticket isn't among the merged ones: it would pass if the page drew a label for a ticket with no `merged_by`.
- The code is right: change only the tests.

### Done when
- a ticket merged with no `merged_by` has a row in While you were away whose text carries no agent name and none of "1st try", "attempt", "lead ticket": it would fail if `_label` gave it one
- a developer ticket merged by `claude-opus` after one developer job that passed reads "1st try" in its row, and not "after 1 developer attempt"
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass (see `docs/workflow.md`)

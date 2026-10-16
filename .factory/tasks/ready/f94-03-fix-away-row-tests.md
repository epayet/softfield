---
id: f94-03-fix-away-row-tests
milestone: f94-opus-f9-25-seeds-and-planting
difficulty: 3
tests_only: true
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f94-opus-f9-25-seeds-and-planting-C2-1
---

### Goal
Fix a checkpoint finding on f94-01-away-row-facts: the new away-row tests pass without checking what the ticket's "Done when" says.

### Context
A should-fix finding by the lead at checkpoint 2, on the merge of ticket f94-01-away-row-facts. In `tests/factory_dashboard/test_overview.py`:
- `test_no_merged_by_shows_no_name_no_label_but_finished_and_took` only asserts that "finished" and "took" appear in the section. It never checks that no name and no label show, so a row that still wrote "Opus" or "1st try" would pass. It also finishes the same job twice (once through a fragile `list(conn.execute(...))[-1]`, then again below); keep one `metrics.finish_job` on the id `start_job` returned.
- `test_title_text_inside_title_only` only asserts the `class="title"` span is non-empty. It never compares the text to the ticket's title, nor checks the title is absent from the `class="how"` span.
- `test_away_developer_ticket_merged_by_opus_after_3_jobs` and `test_away_lead_ticket_shows_lead_ticket` assert `"Opus" in away_text`; "Opus appears once in its row" (the ticket's Done when) is not checked. Count it in that ticket's row (the `away_row` helper at the top of the file returns one row by ticket id).
- `test_finished_shows_day_when_different_day` starts the developer job (23:00) after the escalation that ended the ticket (12:00); give the jobs a start order that matches the story.

### Done when
- the no-`merged_by` test asserts, on that ticket's row, that the agent name and label are absent and that "finished 08:" and "took 10 min" are present
- the title test asserts that each row's `class="title"` text equals that ticket's title and that the title is not in its `class="how"` text
- the two "Opus" tests assert the name occurs exactly once in the ticket's row
- only `tests/factory_dashboard/test_overview.py` changes
- the listed `tests:` pass
- all gates pass

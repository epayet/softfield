---
id: f9-34-fix-away-claude-first-try
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- factory_dashboard/queries.py
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f9-line-polish-C6-1
---

### Goal
Fix a checkpoint finding on f9-15-away-who-did-it: a developer ticket that Claude finished after one failed developer attempt reads "Opus · 1st try", which says the opposite of what happened.

### Context
Found by the lead at a checkpoint, on the merge of `tasks/done/f9-15-away-who-did-it.md`. Read `_label` in `away` in `factory_dashboard/queries.py` and the new `test_away_*` tests in `tests/factory_dashboard/test_overview.py`.
- For `claude-opus` on a developer ticket with one developer job, `_label` returns "Opus · 1st try". In `test_away_ticket_shows_agent_label_and_attempts` the `away-opus` ticket has one *failed* developer job and then an escalation by Opus that passed; the test asserts "Opus · 1st try". The owner asked (2026-10-07) whether Claude did a lead ticket or finished a developer's; this label hides that.
- The existing `test_the_away_panel_follows_since_and_links_each_merged_ticket` was changed to expect "Opus · 1st try" for `away-b`: check its jobs before keeping that text.
- `test_away_no_merged_by_shows_no_label` makes no assertion about the ticket without `merged_by` (it only checks that a qwen name appears), so it would pass without the "no label" rule.

### Done when
- a developer ticket merged by `claude-opus` after one developer job reads "finished after 1 developer attempt", not "1st try"; "1st try" stays for a local agent that merged on its first job
- the no-`merged_by` test asserts that the ticket's row has no `.agent` span and no label text
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 2916
gate_failures: ['stopped']
tokens: 1288956
```

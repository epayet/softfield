---
id: f109-04-merged-page-counts-and-tests
milestone: f109-when-plans-get-merged-i-need
difficulty: 3
finding: f109-03-merged-page-points-on
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
The "Planned: N tickets, M done" link on a merged-away card's page counts one card's tickets the same way for N and M, and the merge tests check what the owner reads.

### Context
Read `_merged_on` and `_merge_links` in `factory_dashboard/planning.py` and `#merged-on`, `a.merged-into`, `a.merged-here` in `factory_dashboard/templates/thread.html`, and the `test_merged_on_*` and `test_merge_links_*` tests at the end of `tests/factory_dashboard/test_planning.py` (f109-01, f109-03).
- `_merged_on` counts tickets with a join over every milestone whose key starts with the kept card's key, but counts the done ones for the first milestone only. A kept card with two milestones (a replan) shows "5 tickets, 1 done" where the truth is more done. Count both over the same milestones.
- The first line of the block shows the bare path `/planning/f95` as the link's text (`thread.html`); the owner asked for plain words: say the card's key and title ("F95, <title>"), as `a.merged-into` does.
- `test_merged_on_lists_open_proposals` ends with two checks that prove nothing: it adds an `approve_plan` request for card `f9` and asserts `"Parallel, said twice" not in html`, a text that is nowhere in that page. Replace them with a real one: a proposal on F95's thread that is applied or rejected is absent from `/planning/f107` (the ticket's own Done when).
- `test_chain_f107_to_f10` asserts `'href="/planning/f10' in html`, which `/planning/f107` also satisfies, so it passes with the chain broken. `test_key_merged_into_two_cards` accepts F13 or F42 and so passes with one of the two missing. Assert the full link (`href="/planning/f10"` with its closing quote) and the visible text of each link, as `test_a_merge_whose_card_left_main_shows_both_ways` does with `response_contains`.
- `_merge_links` wraps its key lookups in `contextlib.suppress(Exception)`; a card file whose name can't give a key should be skipped by name (`ValueError` or whatever `milestone_key` raises), not by hiding every error.

### Done when
- a kept card with two milestones, three tickets done in the second and one ready in the first, shows "Planned: 4 tickets, 3 done"
- the block's first link reads with the card's key and title, with no raw `/planning/` path as its text
- a plan applied or rejected on F95's thread is not listed on `/planning/f107`, and an open one is
- with F107 merged into F10 through F95, `/planning/f107` links to `/planning/f10` exactly and `/planning/f10` shows both "Merged here" lines; a key merged into F13 and F42 shows both links
- the listed tests pass, and fail without the change

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 146877
logs: .softfield/var/runs/20261015-095007/f109-04-merged-page-counts-and-tests
```

```yaml
# --- runner ---
result: done
finished_by: lead
```

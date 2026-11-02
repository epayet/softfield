---
id: f143-02-merges-own-module
agent: lead
milestone: f143-split-test-planning-py-by-page
difficulty: 3
max_diff: 2500                      # a move counts its lines twice: removed and added
depends_on: [f143-01-proposal-page-own-module]
commands: [cp, sed -i]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/merges.py
  - factory_dashboard/proposal.py
  - tests/factory_dashboard/test_planning.py
tests:
  - tests/factory_dashboard/test_merges.py
---

### Goal
Merge links (a merged card's links both ways, "merged on", a message's paths as links) live in their own module, `factory_dashboard/merges.py`, with their tests in `tests/factory_dashboard/test_merges.py`; nothing they do changes.

### Context
Read the Decisions in `.softfield/cards/f143-split-test-planning-py-by-page.md` (D1–D5), and in `factory_dashboard/planning.py` `def _merge_words`, `def _known_cards`, `def _merge_links`, `def _gone_merge`, `def _text_with_links` and `def _merged_on`. f143-01 moved the proposal page to `factory_dashboard/proposal.py` and its tests to a test_proposal.py beside this ticket's: follow how it was done (`git log -1 --stat` on its commit).
- Move those functions to `factory_dashboard/merges.py`. It imports no page module (D4); `planning.py` and `proposal.py` import from it.
- Move to `tests/factory_dashboard/test_merges.py`: the tests under `# --- merge links (f109-01)` in `tests/factory_dashboard/test_planning.py`, up to the first blocked-ticket test (`test_two_blocked_tickets_appear_second_on_the_desk_with_their_ids_and_reasons` stays: it is the desk's), with `response_contains`; the desk's merge tests (`test_an_approved_merge_leaves_the_desk`, `test_a_merge_whose_card_left_main_asks_nothing`) stay too.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`; check with `git diff --stat`.
- Then D5: Grep `.softfield/tasks/ready/`, `.softfield/tasks/later/` and `docs/agents/developer.md` for each moved name and point them at the new files.

### Done when
- the moved tests pass in `tests/factory_dashboard/test_merges.py`, none renamed or edited beyond its imports, and every test left in `test_planning.py` and `test_proposal.py` passes
- a merged card's thread page and the desk show exactly what they did (the moved tests show it)
- no file in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or test beside `factory_dashboard/planning.py` or `tests/factory_dashboard/test_planning.py`
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

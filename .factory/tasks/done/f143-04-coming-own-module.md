---
id: f143-04-coming-own-module
agent: lead
milestone: f143-split-test-planning-py-by-page
difficulty: 3
max_diff: 4000                      # a move counts its lines twice: removed and added
depends_on: [f143-03-thread-page-own-module]
commands: [cp, sed -i]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/coming.py
  - factory_dashboard/overview.py
  - tests/factory_dashboard/test_planning.py
  - docs/agents/developer.md
tests:
  - tests/factory_dashboard/test_coming.py
---

### Goal
The desk's Coming side (what the owner sent that is on its way, a waiting plant's edit and cancel, and Didn't go through) lives in its own module, `factory_dashboard/coming.py`, with its tests and the Plant box's in `tests/factory_dashboard/test_coming.py`; nothing it does changes.

### Context
Read the Decisions in `.factory/cards/f143-split-test-planning-py-by-page.md` (D1–D5), and in `factory_dashboard/planning.py` `def coming`, `def _refused`, `def _failed_edit`, `def _edited`, `def _edit_words`, `def _retried`, `def _taken_plant`, `def _titled`, `def _plant_note`, `def _message_thread` and `def _acted_on`. f143-01 to f143-03 moved three parts the same way: follow their commits (`git log -3 --stat`).
- Move those to `factory_dashboard/coming.py`, with the classes they build (`DeskItem`, `RefusedItem`, `WaitingPlant`, `DeskGroup`) and the small helpers they share with the desk (`_when`, `_card_titles`, `_thread_title`). `coming.py` imports no page module (D4); `planning.py` imports from it. `factory_dashboard/overview.py` and `tests/factory_dashboard/test_overview.py` import `DeskItem` and `_card_titles` from the new home.
- Move to `tests/factory_dashboard/test_coming.py`: the Plant box tests (from `test_the_plant_form_posts_a_plant_request` to `test_a_stored_plant_empties_the_box_even_when_the_new_form_never_comes`), `# --- Coming group (f6-20)`, `# --- "Didn't go through"`, `# --- Try again carries what it retries`, `# --- a waiting plant is edited or cancelled from Coming (F14)`, `# --- an edit that didn't go through` and `# --- liveIdle with a waiting plant (f19-01)`. The desk heading's counts and poll wrapper tests stay in `tests/factory_dashboard/test_planning.py`.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`; check with `git diff --stat`.
- Then D5: Grep `.factory/tasks/ready/`, `.factory/tasks/later/` and `docs/agents/developer.md` for each moved name (`coming`, `_refused`, `_failed_edit`, `_edited`, `test_a_second_plant_adds_a_second_row`, every other moved test) and point them at the new files.

### Done when
- the moved tests pass in `tests/factory_dashboard/test_coming.py`, none renamed or edited beyond its imports, and every test in the other planning test files and `tests/factory_dashboard/test_overview.py` passes
- every test file of D1 is at most 1,500 lines, and every module of D1 at most 600
- the desk shows exactly what it did (the moved tests show it)
- no file in `.factory/tasks/ready/` or `.factory/tasks/later/`, and no worked example in `docs/agents/developer.md`, names a moved `def` or test beside `factory_dashboard/planning.py` or `tests/factory_dashboard/test_planning.py`
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

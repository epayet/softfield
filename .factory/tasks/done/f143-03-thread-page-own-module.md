---
id: f143-03-thread-page-own-module
agent: lead
milestone: f143-split-test-planning-py-by-page
difficulty: 4
max_diff: 4000                      # a move counts its lines twice: removed and added
depends_on: [f143-02-merges-own-module]
commands: [cp, sed -i]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/thread.py
  - factory_dashboard/app.py
  - factory_dashboard/milestones.py
  - tests/factory_dashboard/test_planning.py
  - docs/agents/developer.md
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
A thread's page lives in its own module, `factory_dashboard/thread.py`, with its tests in `tests/factory_dashboard/test_thread.py`; nothing it does changes.

### Context
Read the Decisions in `.factory/cards/f143-split-test-planning-py-by-page.md` (D1–D5), and in `factory_dashboard/planning.py` the section from `# --- a thread (f6-07)` to `def thread_page` and its end (`class Message`, `class Proposal`, `def _header`, `class Review`, `def _review`, `class Standing`, `class ReserveLever`, `def _again`), plus `def _note`, which only the thread page and `factory_dashboard/milestones.py` use. f143-01 and f143-02 moved the proposal page and merge links the same way: follow their commits (`git log -2 --stat`).
- Move that section and `_note` to `factory_dashboard/thread.py`, with its own `router` included in `factory_dashboard/app.py`. `milestones.py` imports `_note` and `_review` from there (they are lazy imports today: keep them lazy). `_repo` stays in `planning.py` (the board uses it).
- Move to `tests/factory_dashboard/test_thread.py` every test that opens a thread's page (`/planning/<card>`): the `# --- thread page fixtures` block, the phone deck (f6-10), the thread's archive buttons, Sign off (F50), a proposal's standing (F31 D3), a waiting message's edit and cancel (f14-03), an open thread's refresh, the reserve lever (F172 D6), a seed's note (f90), and the runner's look on a thread. The desk's own tests (the archived list, the desk's poll) stay in `tests/factory_dashboard/test_planning.py`. `_text`, `_points`, `_open` and `_write` stay in `test_planning.py` and are imported (D3); the fixtures are in `tests/factory_dashboard/conftest.py` since f143-01.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`; check with `git diff --stat`.
- Then D5: Grep `.factory/tasks/ready/`, `.factory/tasks/later/` and `docs/agents/developer.md` for each moved name (`thread_page`, `_header`, `_review`, `_note`, `test_on_a_phone_one_point_shows_at_a_time`, `test_edit_then_save_posts_a_change_and_the_message_shows_it_at_once`, every other moved test) and point them at the new files.

### Done when
- the moved tests pass in `tests/factory_dashboard/test_thread.py`, none renamed or edited beyond its imports, and every test left in the other planning test files passes
- `tests/factory_dashboard/test_thread.py` is at most 1,500 lines and `factory_dashboard/thread.py` at most 600
- a thread's page and a milestone's Sign off answer exactly as before (the moved tests and `tests/factory_dashboard/test_milestones.py` show it)
- no file in `.factory/tasks/ready/` or `.factory/tasks/later/`, and no worked example in `docs/agents/developer.md`, names a moved `def` or test beside `factory_dashboard/planning.py` or `tests/factory_dashboard/test_planning.py`
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

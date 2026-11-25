---
id: bug-68-the-plan-reads-the-pause-from-the-database
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
The factory's plan (`softfield run --dry-run`, and the plan the runner stores for the pages, F279) says the factory is paused only while the owner's pause is open in the metrics database. A copy of an old pause in a project's state file (`State` in `runner/state.py`) doesn't count.

### Context
- On 2026-11-25 the owner resumed at about 08:38: the pause's usage event got its `resets_at` and Softfield's state file (`State` in `runner/state.py`) cleared. The dry run went on saying "Paused by you since 08:05: only planning goes until you resume", because five other projects' state file (`State` in `runner/state.py`) still held `owner_pause` from 08:05. Each copy is rewritten only when the runner next syncs that project (`sync_pause`, at the start of a round in `run_projects`).
- `_project_plan` in `runner/loop.py` loads each project's state (`load_state(cfg.runs_dir / "state.json")`) and passes `state.owner_pause` to `_ProjectPlan` and to `by_the_owner`. `_sentence` then takes the first project with one.
- The truth is `metrics.open_pause` (`runner/metrics.py`). `sync_pause` already follows the same rule: an open event holds, and a pause in the state file whose event is resumed (`metrics.pause_ended`) doesn't. A copy with no event at all still holds, as its docstring says. Use those two functions; don't write state from the plan.
- `test_dry_run_shows_every_line_paused_by_the_owner` and `test_dry_run_says_a_project_paused_by_you_holds_its_tickets` (`tests/runner/test_loop.py`) show how the dry run's tests set a pause.

### Done when
- a project whose state file (`State` in `runner/state.py`) holds an `owner_pause` whose event is resumed in the database is planned as not paused: its tickets aren't "paused by you" and the plan's sentence doesn't say "Paused by you"
- an open pause event holds every project's plan, even one whose state file (`State` in `runner/state.py`) has no `owner_pause`
- a pause in state file (`State` in `runner/state.py`) with no event in the database still holds (as `sync_pause` treats it)
- the two dry-run tests above pass unchanged
- the listed `tests:` pass, and the new ones fail without the change
- all gates pass (see `docs/workflow.md`)

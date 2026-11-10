---
id: f236-03-a-project-that-cant-start-says-why
milestone: f236-softfield-init-adds-a-project-to
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/loop.py
  - runner/gitops.py
tests:
  - tests/runner/test_loop.py
---

### Goal
When the runner can't open a registered project (not on main, or changes not committed), the owner sees it on that project's Planning desk with the reason, instead of the project silently never being worked on.

### Context
Read D7 in `.softfield/cards/f236-softfield-init-adds-a-project-to.md`, then `run_projects` and `open_session` in `runner/loop.py` (the `refused` set and its console line), `is_clean` and `current_branch` in `runner/gitops.py`, and `upsert_owner_item`, `resolve_owner_item`, `open_owner_items` and `find_project` in `runner/metrics.py`; for how another owner item is raised and resolved by the runner, follow an existing caller of `upsert_owner_item` in `runner/loop.py`.
- What happened (2026-11-09): coaster-ranker passed `softfield doctor` at 21:34 and was handed over, but has no row in `runs`; its "Plan this card." job (work_queue 662) waited from 22:38 while later softfield jobs ran, and the Projects page said "nothing for you".
- The item's text, in plain words: "The runner can't start {name}: it isn't on its main branch ({branch})." or "The runner can't start {name}: these changes aren't committed: {paths}." (at most ten paths, then "and N more"), followed by "It tries again every round."
- Keep the console line as it is; the item is said once, like it.

### Done when
- a registered project whose folder has an uncommitted file gets one open `cant_start` item naming that file, and `run_projects` goes on with the other projects
- a project on another branch gets the item naming the branch
- once the folder is clean on main, the next round opens its session and resolves the item
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

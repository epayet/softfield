---
id: bug-63-lead-ticket-catches-up-before-merge
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 4
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A lead ticket whose branch is behind main has main merged in before its check-all and its merge. When the two clash, the ticket is blocked with its work on its branch, and the runner never stops with conflict markers left on main.

### Context
On 2026-11-10 f139-03 resumed its session from 2026-11-09 on its old branch (`_lead_route` and the `interrupted` entry in `run_lead_task`). Main had changed `_plan_branch` in `runner/loop.py` overnight (f235-01's `catch_up_plan`). `_settle_lead_task` ran check-all on the old base, which passed, then `s.git.squash_merge` clashed. The `GitError` was not caught: the run stopped, leaving main's folder half squashed, with markers in `runner/loop.py`, and `softfield run` then failed to import. The lead landed it by hand (commits 1391e8cc and a00b4328).

Read `_settle_lead_task`, `_catch_up` and `block` in `runner/loop.py`. A developer ticket's branch already gets main through `_catch_up` before its gates ("runner: merge main into task/…" commits): follow that. Do it after `commit_all` and before `_check_results`, so check-all runs on the merged tree.

### Done when
- a lead ticket whose branch is behind main and merges cleanly gets main merged in before check-all, and is squashed into main as today
- a lead ticket whose branch clashes with main is blocked with the reason "its work on task/<id> clashes with main", main is clean and checked out, there are no conflict markers anywhere, and the branch keeps its work
- the run goes on to the next pick after that block, without stopping
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

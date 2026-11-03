---
id: f139-03-rebuild-clashing-plan-branches
milestone: f139-the-factory-folder-should-actually-be
agent: lead
difficulty: 7
depends_on: []
finding: f139-the-factory-folder-should-actually-be-F1
files:
  - runner/loop.py
  - runner/requests.py
  - factory_dashboard/proposal.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_requests.py
---

### Goal
A plan branch that clashes with main stops being a dead end: its planner job rebuilds it on main from the plan's own commits, and until then its page and its approval say what to press instead of listing thousands of files.

### Context
Read `_plan_branch` and `_catch_up` in `runner/loop.py`, `plan_range` in `runner/planner.py`, `_approve_plan`, `_outside`, `_put_back` and `_settle_clash` in `runner/requests.py`, and `_plan_changes` and `REFRESH_WORDS` in `factory_dashboard/proposal.py`.
- **The fault, measured on 2026-11-03:** `plan/f133`, `plan/f140`, `plan/f51`, `plan/f82` and `plan/f191` left main before F139's move and got it as one commit (subject "F139: this branch's folder moves to .softfield"). Merged with main they give 95 to 169 conflicts: tickets main finished, moved to `done/`, that the branch's move put in `ready/`, and text both sides changed. So `plan_range` falls back to `main...branch` (2,137 paths for F133), `_outside` refuses, and `_catch_up` fails, so "Refresh against main" drafts on the old branch and nothing repairs it.
- **The rebuild, in `_plan_branch` when `_catch_up` fails:** from main, cherry-pick `main..branch` oldest first with `--no-merges`, skipping that F139 commit, using `-c merge.directoryRenames=true` and `-X theirs`: the older commits name `.factory/`, and rename detection carries them over. Only when every pick succeeds does the branch move, with its old tip kept as `superseded/plan-<card>`. Otherwise abort, and carry on as today with the note.
- The planner then checks the drafts against main, as Refresh already asks. A clash `_settle_clash` accepts stays approvable (f170 D2): only refuse what it wouldn't.

### Done when
- a branch built like `plan/f133` (a draft commit under `.factory/`, the F139 commit, main's move plus a ticket moved from `ready/` to `done/` and a card changed) is rebuilt by its planner job: it merges cleanly with main, `plan_changes` lists only the plan's own files at their `.softfield/` paths, approving it works, and `superseded/plan-f7` holds the old tip
- a replay that fails leaves the branch and main as they were, no `superseded/` branch, and the existing note in the session report
- approving a branch that clashes returns "<branch> clashes with main: press Refresh against main on its page" before `_outside` is asked, and a clash `_settle_clash` accepts is still approved
- a clashing plan's page shows that sentence in place of the changed files' list, with no terminal command
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

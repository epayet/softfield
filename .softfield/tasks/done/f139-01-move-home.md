---
id: f139-01-move-home
milestone: f139-the-factory-folder-should-actually-be
agent: lead
difficulty: 7
depends_on: []
files:
  - runner/home.py
tests:
  - tests/runner/test_home.py
---

### Goal
`move_home` moves one project from `.factory/` to `.softfield/`: its folder, every tracked mention of it, its hook path, its open branches and its rows in the database, and never leaves main half moved.

### Context
Read D1–D4 in `.softfield/cards/f139-the-factory-folder-should-actually-be.md`, then `Git` in `runner/gitops.py`, `runner_commit` and `with_trailers` in `runner/loop.py` (the runner's author and trailers), `check_all` in `runner/checks.py`, the setup's hook path and ignore lines in `runner/setup.py`, and how the desk gets an item in `runner/owner.py`.
- Nothing calls `move_home` yet: f139-02 wires it into the runner's start. Don't change any other file's `.factory` mentions by hand: the move rewrites them when it runs on Softfield.
- `runner/home.py` and `tests/runner/test_home.py` are the only files its text pass skips, so the old name they spell stays.
- Tests build throwaway repos (as `tests/runner/test_setup.py` does) with a `.factory/` folder, an ignored `.factory/var/runs/x/log`, a `.gitignore` line, a file that mentions .factory/cards/a.md, one that has `.card.factory` and `.factory-status`, a `plan/f1` branch with a draft in `.factory/tasks/later/`, and a metrics database (`runner/metrics.py`'s schema) with one row of each kind D4 lists.

### Done when
- after a move: `.softfield/` holds what `.factory/` held, `var/` included, and `.factory/` is gone; the mention reads .softfield/cards/a.md, `.card.factory` and `.factory-status` are unchanged; `git config core.hooksPath` says `.softfield/hooks`; main has one new commit by the runner; `plan/f1` has one commit and its draft is at `.softfield/tasks/later/`; a `superseded/*` branch is untouched
- the database rows of D4 read `.softfield/`, another project's rows and `planner_messages.text` don't change
- when `check_all` fails on the moved tree, the repo is back as it was (folder, files, hook path, no commit) and the desk has an item naming the failed check
- `move_home` returns None, changing nothing, with no `.factory/`, or with both folders (and says so on the desk); a dirty main is refused the same way
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
**Done in the owner's terminal session of 2026-11-02.** Commit: "F139: <project>'s folder moves to .softfield, in Softfield, Coucou and Travel Companion".

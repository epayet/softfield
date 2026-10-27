# Milestone F121: Projects on any main branch, in any language

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

Make `softfield init` and the gates work on any repo.

**Main branch.** The factory assumes a branch called `main` everywhere (`MAIN` in runner/loop.py,
runner/planner.py, `setup.init`). Setting up a copy of fact-printer (which is on `master`) was
refused; `init` now says to rename the branch. Proposed: `[project] main = "master"` in
`.factory/project.toml`, read wherever `MAIN` is used.

**Check commands.** check-all and the gates still run Python's tools, whatever the project:
- lint: `uv run ruff check .` and `ruff format --check .` (runner/checks.py, `gate_ruff`);
- auto-format before the gates: ruff on changed `.py` files (`gates.autoformat`);
- a ticket's tests and the suite: `uv run pytest` (`gate_task_tests`, `gate_all_tests`);
- "new tests fail without the change": pytest's exit codes 1/2 and 5 (`gate_tests_fail_on_main`);
- no new skips: pytest's skip/xfail patterns (`gate_no_new_skips`);
- one test file per module: `test_x.py` ↔ `x.py` (`layout_problems`);
- what the local developer may run: `agents.CHECK_COMMANDS` and `opencode.json`.
Already stack-free: protected paths, diff size, dependency files, BLOCKED.md, planning, reviews.

Proposed `[checks]` keys, Python with uv staying the default so Coucou and Softfield don't change:
```toml
lint = ["npm", "run", "lint"]
format = ["npx", "prettier", "--write"]   # on the changed files before the gates
test = ["npx", "vitest", "run"]           # a ticket's tests appended; the suite gets test_dirs
skip_patterns = ['\.skip\(', '\.only\(']
```
"Tests fail on main" becomes: any non-zero exit means they failed. Proof: one small JavaScript
project set up with `softfield init`. About one session of protected runner code.

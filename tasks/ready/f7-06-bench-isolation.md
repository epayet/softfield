---
id: f7-06-bench-isolation
milestone: f7-factory-fixes
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/bench.py
tests:
  - tests/runner/test_bench.py
commands: [opencode run]
---

### Goal
A benched OpenCode agent reads, edits and runs commands only in its own copy, and every bench proves it: the main checkout is unchanged when the bench ends.

### Context
Read `runner/bench.py` (its docstring: f2-12 moved benches from worktrees to clones, f4-19 gave each copy a new root commit), `_clone` and `make_copy`, and `runner/local_model.py` (how `opencode run` is started, its cwd and environment). Test-first.
- **On 2026-10-04 it still leaked** (`var/bench/bench-20261004-204145/*/opencode-*.jsonl`): the agents' `filePath`s were absolute paths under the main checkout (`tests/factory_dashboard/test_overview.py`, `factory_dashboard/templates/_partials/running.html`), pytest reported the main checkout as its root, gemma4 wrote its BLOCKED file there, and the copies stayed unchanged, so every attempt failed. The agent process's cwd was the copy.
- Find how OpenCode chose the main checkout (its project store under `~/.local/share/opencode`, keyed how; an environment variable; `opencode.json`), and fix the copy or the call so it can't. A real `opencode run` in a scratch copy (the `commands:` above) is the probe; record what you found in the docstring.
- **The canary:** `runner bench` records `git status --porcelain` of the main checkout before and after each replay; any change stops the bench with the files named, and the replay counts as void, not failed.

### Done when
- a test: a replay whose agent writes a file outside its copy stops the bench, names the file, and records the replay as void
- a probe with a real `opencode run` in a copy edits only the copy (its result noted in `docs/milestones/f7-factory-fixes.md`)
- `uv run runner check-all --task f7-06-bench-isolation` passes

---
id: f2-12-bench-isolation
milestone: f2
depends_on: []
agent: lead
difficulty: 6
files:
  - runner/bench.py
  - runner/config.py
  - docs/workflow.md
tests:
  - tests/runner/test_bench.py
---

### Goal
A bench agent works in a copy of the repo that has nothing to do with the main checkout, so it can neither read nor change the owner's working tree.

### Context
Read `runner/bench.py` (`make_worktree`, `remove_worktree`, `bench_dir`, `_overlay`, `OVERLAY`), `runner/local_model.py` (`run_opencode`: its working directory) and `opencode.json` (the permissions: edits anywhere in the project).
- **What happened (2026-10-02):** the owner's bench (`var/bench/bench-20261002-102018/`) ran `ollama-gpt-oss-120b` and `ollama-nemotron-3-super` on f1-36. Their OpenCode logs (`opencode-1.jsonl`) edited `/home/manu/projects/epayet/coucou/factory_dashboard/templates/tickets.html`, `tests/factory_dashboard/conftest.py` and `tests/factory_dashboard/test_tickets.py` in the main checkout, while their worktree stayed clean, so the gates saw nothing. The lead reverted the main checkout by hand.
- **Likely cause, to confirm with a test:** a `git worktree` shares the main repo's `.git` (`git rev-parse --git-common-dir`), and OpenCode takes the project root from it, so the main checkout is the project. A worktree inside `var/` makes it worse, but moving it alone may not fix it.
- **The fix:** each bench copy is its own clone (`git clone --local --no-checkout` of the repo, then the parent commit checked out, the overlay copied and committed as today), under `[bench] dir` in `workflow/runner.toml`, default `~/.cache/software-factory/bench/` (outside any repo; `~/.cache` because a copy holds a `.venv` of a few hundred MB, and `/tmp` may be RAM). The clone has its own `.git`, so OpenCode's project is the clone, and `opencode.json`'s permissions (copied by the overlay) apply there.
- **The test:** a fake OpenCode (a script on `PATH` in the test) that resolves its project the way OpenCode does (`git rev-parse --show-toplevel` and `--git-common-dir` from its working directory) and writes a file there; after a bench attempt, the main checkout is unchanged and the file is in the copy.
- Remove the copy afterwards, as now; keep the logs under `var/bench/`.

### Done when
- a bench attempt's edits land in its own copy, and the main checkout's `git status` is unchanged (the fake OpenCode test)
- the copy lives under the configured `[bench] dir`, outside the repo, and is removed afterwards
- `uv run runner check-all --task f2-12-bench-isolation` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

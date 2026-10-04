---
id: f4-19-bench-own-project
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 4
files:
  - runner/bench.py
tests:
  - tests/runner/test_bench.py
commands: [opencode]
---

### Goal
Each bench copy is a project of its own for OpenCode, so a benched agent reads and edits only its copy, never the main checkout.

### Context
Read `runner/bench.py` (`_clone`, its module docstring on f2-12) and `tests/runner/test_bench.py`. Test-first.
- **What happened (2026-10-02, 22:25):** `runner bench f1-38-project-page-fixes m4-11-send-once --agents …` edited `/home/manu/projects/epayet/coucou/factory_dashboard/projects.py` and three more files in the main checkout. Every attempt then failed "no-changes" in its copy.
  - The logs are in `var/bench/bench-20261002-222557/`: see the `filePath`s in `opencode-1.jsonl`.
  - The lead restored the checkout.
- **Why:** OpenCode keys a project by the repo's root commit, and keeps one worktree per project in `~/.local/share/opencode/opencode.db`. The `project` row `efc5948832938a7b25931c4ecb5e50dc61d72ad9` points at the main checkout. A `--local` clone has the same root commit, so its session's `directory` is the main checkout.
- **Make the copy a different project:** for example, after the checkout at `at`, replace its history with one new root commit holding that tree. Check whatever the gates and the attempt loop need from the copy's history (a base to diff against). Prove it with one real `opencode` call in a scratch copy: its session's directory must be the copy.
- Add a test that a bench copy's root commit differs from the main repo's. Update the module docstring.

### Done when
- a bench copy has its own root commit, and the gates still compute the attempt's diff in it
- a real OpenCode session started in a copy records the copy as its directory (checked once by hand, written in the job's notes)
- `uv run runner check-all --task f4-19-bench-own-project` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

---
id: bug-55-bench-replays-from-before-the-move
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
finding: f139-the-factory-folder-should-actually-be-F3
files:
  - runner/bench.py
tests:
  - tests/runner/test_bench.py
---

### Goal
A bench replay of a ticket merged before F139's move runs its gates instead of crashing for lack of `.softfield/protected-paths.txt`.

### Context
`make_copy` checks out the old tree, which has `.factory/`, then lays `OVERLAY` over it. `OVERLAY` in `runner/bench.py` holds `.softfield/project.md`, `.softfield/developer.md` and `.softfield/opencode.json`, not the protected paths, so `read_protected(work)` in `_attempts` raises `FileNotFoundError` on any such tree.
Fix: add `.softfield/protected-paths.txt` to `OVERLAY`. Leave the old tree's `.factory/` as it is: its own code and tests still name it.

### Done when
- a copy made from a tree with `.factory/` and no `.softfield/` has `.softfield/protected-paths.txt`, with the repo's text, and `read_protected` reads it
- that tree's `.factory/` is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

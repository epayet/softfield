---
id: bug-15-fix-scope-names-the-last-round
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 40
finding: f53-F3
files:
  - runner/milestone.py
tests:
  - tests/runner/test_milestone.py
---

### Goal
A later review round that lists its milestone's merges also lists the review's own last-round commit.

### Context
Read `def _fix_scope` in `runner/milestone.py` and its tests in `tests/runner/test_milestone.py`. `runner/**` is protected: tests first.
- When another milestone's ticket merged between two rounds, `_fix_scope` lists only the `Task:` merges of its own milestone. The review's own last-round commit (its direct fixes and the tickets it wrote) is left out, though `git diff since..main` had it.
- Add it to the list as ``the last round: `git show <sha>` ``.

### Done when
- round 2 after another milestone's merge lists its own merges and the last round's commit
- round 2 with no other merge in between reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: bug-46-ratings-replay-test-reads-the-line
milestone: bugs
difficulty: 2
depends_on: []
area: factory
priority: 74
finding: f7-factory-fixes-F3
tests_only: true
files:
  - tests/runner/test_cli.py
tests:
  - tests/runner/test_cli.py
---

### Goal
`test_ratings_replay_twice_gives_the_same_ratings` checks the line the replay prints for the local model.

### Context
Read `test_ratings_replay_twice_gives_the_same_ratings` in `tests/runner/test_cli.py` and the `ratings --replay` output in `runner/cli.py`. The code is right; since f7-02 the test checks only that some `replay ADR 24` rows exist and that `→` appears once.
- Assert the printed line for `local-qwen3.6-35b-a3b`: its rating before, after, and its game count, as the old test did with "2 tickets replayed from 5"; and that the second replay prints the same line.

### Done when
- the test fails if the local model's before, after or game count is wrong (check by changing the fixture's outcome by hand once, and putting it back)
- the second replay's line equals the first's
- all gates pass (see `docs/workflow.md`)

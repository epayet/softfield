---
id: bug-19-voiding-benches-recomputes-ratings
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 45
finding: f7-factory-fixes-F5
files:
  - runner/cli.py
tests:
  - tests/runner/test_cli.py
---

### Goal
`softfield ratings --void-benches-before` leaves the stored ratings without the voided games.

### Context
Read the `ratings` command in `runner/cli.py` (`--void-benches-before`, `--replay`) and `def void_benches_before` in `runner/loop.py`, and `test_ratings_replay_twice_gives_the_same_ratings` in `tests/runner/test_cli.py`. `runner/**` is protected: tests first.
- Today the void without `--replay` voids the jobs but leaves the stored ratings with those games in them, and says nothing. Make the void imply the replay.
- No CLI test covers the flag, nor its refusal of a time without a zone: add both.

### Done when
- `--void-benches-before <time>` alone voids the jobs and replays: the ratings printed match a run with both flags
- a time with no zone is refused with "give its time zone", and nothing is voided
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

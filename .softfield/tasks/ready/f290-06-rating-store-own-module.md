---
id: f290-06-rating-store-own-module
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 4
max_diff: 4000                      # a move counts its lines twice: removed and added
depends_on: [f290-05-lead-job-own-module]
commands: [cp, sed -i]
files:
  - runner/loop.py
  - runner/rating_store.py
  - runner/ratings.py
  - runner/session.py
  - runner/developer_job.py
  - runner/milestone.py
  - runner/cli.py
  - runner/bench.py
  - tests/runner/test_loop.py
  - tests/runner/test_bench.py
tests:
  - tests/runner/test_rating_store.py
---

### Goal
Reading and writing the agents' ratings in the metrics database (starting ratings, standings, a ticket's, a review's and a bench's games, the replay) lives in `runner/rating_store.py`, with its tests in `tests/runner/test_rating_store.py`; `runner/ratings.py` stays the pure maths, and nothing the runner does changes.

### Context
Read the Decisions in `.softfield/cards/f290-runner-loop-py-is-6-500.md` (D1–D8), and follow f290-05's commit (`git log -1 --stat`).
- The candidates in `runner/loop.py`: from `def starting_ratings` to the end of `def rate_finished` (`def standing`, `def routing_ratings`, `def rate_ticket`, `def rate_verdicts`, `def rate_bench`, `class Replayed`, `def replay_ratings`, `def void_benches_before`), plus `def current_ratings` if f290-01 left it, applying D3.
- `runner/cli.py` calls `loop.starting_ratings`, `loop.standing`, `loop.replay_ratings` and `loop.void_benches_before`; `runner/milestone.py` imports `rate_verdicts` and `starting_ratings`: point them at `runner/rating_store.py`.
- Fix the docstring at the top of `runner/ratings.py`, which says the runner writes `rating_changes` in `runner.loop`: it is `runner.rating_store` now.
- `rating_store` sits under the job modules (D4): it imports `runner/session.py` only.
- Then D7 for each moved name.

### Done when
- `runner/rating_store.py` holds the ratings' database side and imports only `runner/session.py` of the split modules; `runner/ratings.py` is unchanged but for its docstring
- the moved tests pass in `tests/runner/test_rating_store.py`, none renamed or edited beyond imports and patch targets, and every other test in `tests/runner/` passes
- no ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or `class` beside `runner/loop.py`
- all gates pass (see `docs/workflow.md`), mypy included

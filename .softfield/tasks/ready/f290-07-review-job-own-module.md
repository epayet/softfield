---
id: f290-07-review-job-own-module
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 5
max_diff: 6000                      # a move counts its lines twice: removed and added
depends_on: [f290-06-rating-store-own-module]
commands: [cp, sed -i]
files:
  - runner/loop.py
  - runner/review_job.py
  - runner/session.py
  - runner/developer_job.py
  - runner/milestone.py
  - tests/runner/test_loop.py
  - tests/runner/conftest.py
  - tests/runner/test_milestone.py
tests:
  - tests/runner/test_review_job.py
---

### Goal
The runner's reviews short of the milestone review (checkpoints, shadow and stand-in checkpoints, the pre-review, fix tickets, findings and the merges they cover) live in `runner/review_job.py`, with their tests in `tests/runner/test_review_job.py`; nothing the runner does changes.

### Context
Read the Decisions in `.softfield/cards/f290-runner-loop-py-is-6-500.md` (D1–D8), and follow f290-06's commit (`git log -1 --stat`).
- The candidates in `runner/loop.py`: from `def _done_milestone` to the end of `def record_findings` (`def under_review`, `def _drop_covered_merges`, `def note_merge`), and from `def _authors` to the end of `def fix_ticket` (`def checkpoint`, `def shadow_checkpoint`, `def _read_only_review`, `def stand_in_checkpoint`, `def pre_review`, `def pre_review_pick`, `def _pre_review_turn`, `def fix_tickets`), plus `def _name_checkpoint`, `def checkpoint_reason` and `def review_reason` if f290-01 left them, applying D3.
- `runner/milestone.py` imports `record_findings` and `review_reason` from the loop and is imported back by these functions inside them (`due_reviews`, `_done_tickets`, `signed_off`): keep those imports inside the functions (D4).
- D5: `pre_review` is patched on `loop` by the scheduler's tests; they keep patching it there if the scheduler calls it.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`; check with `git diff --stat`.
- Then D7 for each moved name.

### Done when
- `runner/review_job.py` holds those reviews, at most 1,800 lines, and does not import `runner/loop.py` at module level
- the moved tests pass in `tests/runner/test_review_job.py`, none renamed or edited beyond imports and patch targets, and every other test in `tests/runner/` passes
- no ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or `class` beside `runner/loop.py`
- all gates pass (see `docs/workflow.md`), mypy included

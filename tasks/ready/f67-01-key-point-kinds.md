---
id: f67-01-key-point-kinds
milestone: f67-in-proposals-sometimes-i-see-d1
difficulty: 4
depends_on: [f31-03-point-outcomes]
agent: lead
files:
  - runner/planner.py
  - runner/prompts.py
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_prompts.py
---

### Goal
A proposal's key points in the planner's reply block may say their kind (`info`, `attention`, `choice`), and a choice carries its options and the lead's pick; the planner prompt asks for them, information first, in plain words.

### Context
Read `docs/milestones/f67-in-proposals-sometimes-i-see-d1.md` D1, D3, D4 and D5. In `runner/planner.py`: `_proposal` and `_numbered`; in `runner/prompts.py`: `_PLANNER_TAIL` (the `key_points` line of the example block) and `_PLANNER_HEAD`.
- `kind` is optional; when given, one of `info`, `attention`, `choice`. A key point with `flag: true` and `kind: info` is refused (a flagged point needs a look).
- A `choice` has `options`, a list of 2 to 4 objects with `label` and `text` as strings, and `pick`, a whole number indexing one of them. `options` or `pick` on a point that isn't a `choice` is refused.
- The prompt: give each key point its kind; number the `info` points first, then `attention`, then `choice`; an open question between options is a `choice` with the recommendation as `pick`; never put a decision or ticket number ("D2", "f31-03") in a key point in place of words.
- **A reply block that was read before this change is read the same way after it.**

### Done when
- a block whose key points carry each kind, and a choice with 2 to 4 options and a valid `pick`, is read
- a block with an unknown kind, a choice with 1 or 5 options, a `pick` out of range, `options` on an `info` point, or a flagged `info` point is not read, with a note naming the point
- a block without `kind` reads as today
- the prompts hold the new rules (the tests read each)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

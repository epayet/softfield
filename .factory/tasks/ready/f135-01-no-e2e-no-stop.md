---
id: f135-01-no-e2e-no-stop
milestone: f135-why-is-there-a-couple-of
depends_on: []
agent: lead
difficulty: 1
priority: 1
area: factory
files:
  - runner/milestone.py
tests:
  - tests/runner/test_milestone.py
---

### Goal
A milestone review of a project with no `tests/e2e/` runs its rounds instead of stopping at once with "end-to-end tests fail on staging", and the reviews that stop already cut short (F28, F19) become due again.

### Context
Read "What we know" and Decisions D1–D2 in `.factory/cards/f135-why-is-there-a-couple-of.md`. In `runner/milestone.py`: `_e2e`, `review_milestone` (the `stop = "end-to-end tests fail on staging"` branch), `_reviewed` and `due_reviews`. In `runner/loop.py`: `run_e2e` (don't change it). In `tests/runner/test_milestone.py`: the tests that patch `milestone.run_e2e`, and `test_a_reviewed_or_signed_off_milestone_isnt_due_again`.
- The e2e stop's words are what the runner's state (`review_stop`) holds for F28 and F19: compare against one constant, not a second spelling.
- `runner/owner.py` already resolves a milestone's review-stop item when its next verdict no longer names it: don't change it.

### Done when
- with no `tests/e2e/` in the repo, a review round calls no `run_e2e`, logs that there are no end-to-end tests, and goes on to Claude's round
- with `tests/e2e/` present, the run and its stop on failure are as today
- a milestone whose recorded stop is the e2e stop is due again when the repo has no `tests/e2e/`, and not due when it has one; other stops are unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

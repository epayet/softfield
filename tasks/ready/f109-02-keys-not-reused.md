---
id: f109-02-keys-not-reused
milestone: f109-when-plans-get-merged-i-need
difficulty: 3
depends_on: []
agent: lead
files:
  - runner/planner.py
  - runner/requests.py
tests:
  - tests/runner/test_planner.py
---

### Goal
A plant never takes the key of a card that has a planning thread, so a card merged away keeps its key and its thread to itself.

### Context
Read `docs/milestones/f109-when-plans-get-merged-i-need.md` (D4, D5). In `runner/planner.py`: `next_key` counts the keys of the docs in `docs/milestones/` and of the tickets only. In `runner/requests.py`: `_plant` calls it, and `_merge` removes the duplicate's doc. In `runner/metrics.py`: `thread_cards` lists every thread's card.
- F64 was planted and merged three times, F73 and F107 twice: each time the card was the highest, its doc left main and the next plant took its key, so `/planning/f64` holds three conversations.
- `next_key` takes the keys already taken elsewhere as a third argument (empty by default); `_plant` gives it the threads' cards. `general` and a key of another series are passed over.
- The test to follow: `test_the_next_key_is_the_one_after_the_highest_in_the_areas_series`, and `test_two_ideas_planted_at_one_pick_take_two_keys` for a plant through the request.
- **Protected work: test-first.**

### Done when
- with docs up to F8 and a thread on `f9` (its card merged away), the next factory plant is F10
- a thread on `general`, or on `m9` for a factory plant, changes nothing
- with no threads, the next key is as today
- two ideas planted at one pick still take two keys
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

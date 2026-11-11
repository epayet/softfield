---
id: f85-08-ripe-pictures-follow-the-setup
milestone: f85-when-i-sign-off-a-task
agent: lead
difficulty: 4
depends_on: [f85-06-fix-unstyled-page-not-a-picture]
files:
  - runner/shots.py
  - runner/loop.py
tests:
  - tests/runner/test_shots.py
  - tests/runner/test_loop.py
---

### Goal
A card waiting for its sign-off gets new pictures, with no Claude job, once its project's `[shots]` or its list of pages has changed since its pictures were taken: a fixed setup shows on the card before the owner signs it off.

### Context
Read D5 and D14 and "Unstyled and missing pictures" in `.softfield/cards/f85-when-i-sign-off-a-task.md`. Then `_take`, `take` and the list file they write (shots.json, `LIST_FILE`) in `runner/shots.py`, `project_shots` in `runner/config.py`, and in `runner/milestone.py` `due_reviews`, `_reviewed` and `signed_off`. In `runner/loop.py`, the round each project gets at a pick (`project_round`).
- The list file gains `setup`: a fingerprint of the project's `[shots]` values as read by `project_shots` (not the file's text, so a comment changes nothing). `_take` writes it.
- `stale(repo, key) -> bool` in `runner/shots.py`: the card lists pages, its project has `[shots]`, and the list file is missing, has no `setup`, or its `setup` or `pages` differ from now. A failed picture alone doesn't make it stale.
- At each pick, before the project's work, a card that is reviewed and not signed off and `stale` gets `take` with its start tag as the base, logged in one line. One card per pick at most, so a pick isn't held up for long.
- When the start tag is gone, the before is recorded with its reason, as today.

### Done when
- a ripe card whose list file has no `setup` gets new pictures at the next pick, and none at the pick after
- changing `serve` in the project's `[shots]` makes it stale; a comment added to the file doesn't
- a ripe card whose pictures failed with the setup unchanged gets none at the next pick
- a card signed off, or still being built, gets none
- the listed `tests:` pass, and fail without the change
- all gates pass (see `runner/instructions/workflow.md`)

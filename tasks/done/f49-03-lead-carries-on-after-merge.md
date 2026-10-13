---
id: f49-03-lead-carries-on-after-merge
milestone: f49-don-t-ask-me-to-merge
difficulty: 4
depends_on: [f49-01-auto-merge]
agent: lead
files:
  - runner/requests.py
  - runner/planner.py
  - runner/loop.py
  - runner/prompts.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
  - tests/runner/test_prompts.py
---

### Goal
After a merge the lead carries on on the kept card by itself, so the owner is never asked to write "go" on another page.

### Context
Written after the work, for the record: done by the lead in the terminal session of 2026-10-13 with the owner (`eda0843`), who asked that F107 not happen again before the session ended. Read `docs/milestones/f49-don-t-ask-me-to-merge.md` D7.
- F107's number went to two notes, both merged away; its page had no card, and three replies there ended in "write go on F73" or "on F95".
- **Protected work: test-first.**

### Done when
- after a merge the owner approved on the duplicate's thread, the kept thread holds the duplicate's notes as the owner's message ("From F12, merged here: …") and a planner job is queued on the kept card
- the same after a merge the lead applied on its own, in the same run; a merge proposed on the kept card's own thread queues nothing more
- a message written on the thread of a card merged into one card goes to that card's thread, and the old thread says where it went; with two kept cards, or a card on main again, it stays
- both planner prompts say: on a duplicate, only which card it repeats; never ask the owner to write on another page
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

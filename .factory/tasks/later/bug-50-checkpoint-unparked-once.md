---
id: bug-50-checkpoint-unparked-once
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
finding: f151-i-had-to-restart-the-runner-F2
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
`note_merge` starts the parked checkpoint again only on the merge that reaches `checkpoint_every`, not on every merge past it.

### Context
From the old backlog file, in the review's words:

`note_merge` (`runner/loop.py`) starts the parked checkpoint again on every developer merge at or past `checkpoint_every`, not only the one that reaches it: when the stand-in may not run (past its cap) each merge adds another "No checkpoint stand-in may run now" note to the session report, and a stand-in whose job fails is paid again each merge. Harmless while F140 is pending; if it shows up, unpark only when `len(unchecked)` is a multiple of `checkpoint_every`, or drop the branch when F140 removes the park after a stand-in. Stays: F140 may remove the branch; a ticket only if the note shows first.

### Done when
- a merge past `checkpoint_every` while the checkpoint is parked leaves it parked, and the merge that reaches it starts it
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

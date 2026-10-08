---
id: f31-03-point-outcomes
milestone: f31-when-i-click-on-approve-plan
difficulty: 6
depends_on: []
agent: lead
files:
  - runner/planner.py
  - runner/prompts.py
  - runner/loop.py
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_prompts.py
  - tests/runner/test_loop.py
---

### Goal
The planner's reply block gives each point an outcome and, on a seed card's first reply, the card's title; the planner prompt asks for short prose, named cards, and no round trip for a bare "agreed".

### Context
Read `docs/milestones/f31-when-i-click-on-approve-plan.md` D4, D6 and D7 (the `title` part). In `runner/planner.py`: `parse_reply`, `_checked`, `_numbered` and `Reply`; in `runner/prompts.py`: `_PLANNER_HEAD`, `_PLANNER_TAIL`, `PLANNER` and `PLANNER_GENERAL`; in `runner/loop.py`: where the planner's reply is stored (the call to `planner.parse_reply`).
- `outcome` is optional and checked: one of `info`, `ticket`, `adr`, `mockup`, `roadmap`, `merge`, `question`; `proposal`, when given, names an id in the same block. A bad one makes the block unread, as any bad field does today.
- `title` (top level, optional): when the thread's card is still `idea` on main, the runner rewrites only its heading (`# Milestone F32: <title>`) and its `milestones` row's title, in a commit of its own, `F32 named by the lead`; the file name stays. On any other card it is ignored. A title over 80 characters or with a newline is ignored, with a note.
- The prompt (D6): prose before the points is at most two lines; a card is always named with its title; a bare "agreed" or "go" with nothing new gets one point saying the plan waits for Approve; on a seed card's first reply, give `title`.
- **The heading is the only line of main the planner's reply changes, and only through the runner.**

### Done when
- a block whose points carry each outcome is read, and one with an unknown outcome or a `proposal` id not in the block is not
- a reply with `title` on an idea card renames its heading and its board row in one commit; the file and the key stay; on a ready card it changes nothing
- a reply without `title` or outcomes reads as today
- the prompts hold the new rules (the tests read each)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

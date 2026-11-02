---
id: f147-01-clash-keeps-the-work
milestone: f147-what-happens-to-checkpointing-and-wip
depends_on: []
agent: lead
difficulty: 4
area: factory
files:
  - runner/loop.py
  - runner/prompts.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_prompts.py
---

### Goal
When a developer ticket's branch clashes with main and is reset, its work is saved first as `clash.diff` in its logs, and the direction and the last attempt are told about the clash and read that diff, so the work is reapplied instead of lost.

### Context
Read "What the code does", Done when and Decisions D1–D2 in `.softfield/cards/f147-what-happens-to-checkpointing-and-wip.md`.
In `runner/loop.py`: `_start_attempt`, `_catch_up`, `run_task` (the `reset_at_start = _start_attempt(s, branch, "")` line and the attempt loop after it), `give_direction`, `_prompt`, `_direction_needs`. In `runner/gitops.py`: `fresh_branch` (don't change it). In `runner/prompts.py`: `RESET`, `DIRECTION`, `FRESH`, `DIRECTED`.
- Save the diff of the branch's own work (`main...task/<id>`, i.e. against the merge base), taken before `fresh_branch` runs. Every clash goes through `_start_attempt`, including the one at the top of `run_task`.
- A clash found at the top of `run_task` must reach the attempt that follows: the direction (if one is due) and the developer's prompt (`prompts.RESET["conflict"]`). Today `reset_at_start` only feeds the regate.
- A clash adds a report note and a job note containing "clashed with main".

### Done when
- a ticket whose branch clashes with main on resume leaves `clash.diff` in its logs holding the branch's own changes, and the branch is reset to main as today
- the direction it gets after that clash is told the branch was reset for a clash and is pointed at `clash.diff`, and its `last.diff` isn't presented as the work
- the last attempt's prompt says the branch was reset for a clash and names `clash.diff` to reapply; with no clash, the prompts are as today
- a clash on a later attempt (the reset inside the attempt loop) saves `clash.diff` too
- the run report has a "clashed with main" note for the ticket
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

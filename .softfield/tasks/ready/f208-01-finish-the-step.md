---
id: f208-01-finish-the-step
milestone: f208-there-s-been-a-few-no
depends_on: []
agent: lead
difficulty: 3
area: factory
files:
  - runner/local_model.py
tests:
  - tests/runner/test_local_model.py
---

### Goal
A developer attempt with no edit at minute 20 finishes the step it is on, up to minute 35, instead of being cut in the middle of a thought, and a stopped attempt's thinking is kept beside its log.

### Context
Read "What we know" and Decisions D1 and D2 in `.softfield/cards/f208-there-s-been-a-few-no.md`. In `runner/local_model.py`: `NO_EDIT_AFTER`, `STOP_NO_EDIT`, `stuck`, `run_opencode` and its `tick`, `parse_events` (`steps` counts `step_finish` events), `stream_facts`, `session_reasoning`. In `tests/runner/test_local_model.py`: `_ticking`, `_step`, `test_a_stream_with_no_edit_for_20_minutes_is_stopped` and the test beside it where an edit lets the attempt run on.
- A step's `step_start` reaches the stream only when the model starts writing, so during a long prompt the last event is the previous `step_finish`. Count finished steps rather than looking at the last event: the step in hand is whatever finishes after minute 20, a prompt still being read included.
- An attempt's thought is only saved when its step ends (see `.softfield/var/runs/20261103-110556/f170-04-blocked-ticket-page/thinking-3.md`, which stops at the step before the cut), so whatever is saved at the stop holds the finished steps only.
- The stop's words stay `STOP_NO_EDIT`, "stopped: no edit after 20 min": `stop_reason` compares them, and they stay true.
- `_save_thinking` in `runner/loop.py` keeps writing its files before a direction or an escalation, with the same names and the same text: it may overwrite what this writes. Don't change it.
- The repeat stop (`STOP_REPEATING`) and the attempt's own limit (`[timeouts] opencode`) don't change.

### Done when
- an attempt with no edit that finishes no further step after minute 20 runs on at minute 34 and is stopped at minute 35 with `STOP_NO_EDIT`, in its result and in its log's marker
- an attempt with no edit that finishes a step at minute 24 is stopped at the first tick after that step, not at minute 35
- an attempt whose step in hand at minute 20 makes its first edit at minute 30 is not stopped, and runs on to its end
- an attempt that edited before minute 20 is never stopped by this rule
- an attempt stopped with `STOP_NO_EDIT` or `STOP_REPEATING` leaves `thinking-N.md` next to its `opencode-N.jsonl` (a rerun's `opencode-N-M.jsonl` leaves `thinking-N-M.md`) holding `session_reasoning` for its session; with no reasoning found, no file is written and the stop still happens
- the comment above `NO_EDIT_AFTER` says why the step finishes and why 35: F208, today's two stops were cut 14 and 15 minutes into one thought
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

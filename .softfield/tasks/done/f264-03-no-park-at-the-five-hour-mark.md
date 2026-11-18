---
id: f264-03-no-park-at-the-five-hour-mark
milestone: f264-the-factory-should-never-stay-idle
depends_on: [f264-01-lead-fills-the-gap]
agent: lead
difficulty: 3
area: factory
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
Nothing waits at Claude's 5-hour mark any more: a lead ticket no longer parks there, a review, direction, escalation or checkpoint no longer waits there, and its desk item goes; only the window's real limit (100%) or a rest after a refusal holds Claude's work (ADR 50 items 3 and 4).

### Context
Read "Settled with the owner" and D5 in `.softfield/cards/f264-the-factory-should-never-stay-idle.md` and `.softfield/adr/50-the-line-never-idles-for-the-pace.md`. In `runner/loop.py`: `at_five_hour`, `_at_five_hour`, `FIVE_HOUR_KIND`, `FIVE_HOUR_HELD`, `_end_unbegun_parks`, `choose_ticket` (its `unbegun` list), `claude_hold` (its `owners` keyword and `five_on`), `_wait_for_reset` (its `held` and `until=`), `_five_hour_switched_on`, and how ADR 44 cleared `at_reserve` parks at the start of a run (search `RESERVE_KIND`). The tests that park at the 5-hour window are in `tests/runner/test_loop.py` (search `five_hour` and `FIVE_HOUR`).
- f264-01 already lets a lead ticket fill the gap past the 5-hour mark in `choose_ticket`; this ticket removes the park that would still stop it at `at_five_hour` in the ticket's run.
- The 5-hour switch stays: `windows.reserves` still reads it, and with it on lead tickets keep the board's order (D2). Its owner-item words change in f264-02, not here.
- A job cut off mid-work by the real limit still parks and resumes at its reset (ADR 44 item 7): don't touch those parks.
- Tests that check a park at 75% change with this rule: rewrite them to check that the ticket or job goes on, and that 100% still holds it.

### Done when
- with the 5-hour window at 80%, nothing else to run and the switch off, the runner starts the first lead ticket: no park in `state.parked`, no owner item of the 5-hour kind
- with the 5-hour window at 80%, `claude_hold` returns None for a review, a direction, an escalation and a checkpoint; at 100%, or with the window resting, it holds them as today
- a run that starts with a `FIVE_HOUR_KIND` entry in `state.parked` drops it and resolves its open owner item
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

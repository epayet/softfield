---
id: f219-01-one-lead-rule
milestone: f219-lead-tickets-don-t-wait-on
agent: lead
difficulty: 6
depends_on: []
files:
  - runner/allowance.py
  - runner/dispatch.py
  - runner/loop.py
tests:
  - tests/runner/test_allowance.py
  - tests/runner/test_dispatch.py
  - tests/runner/test_loop.py
---

### Goal
Lead tickets follow Claude's week pace line for real, may use the whole reserve in the week's last 10%, and the runner and `softfield run --dry-run` choose the next ticket with the same code.

### Context
Read `.softfield/adr/44-lead-tickets-stop-at-the-reserve.md` and D1 to D6 in `.softfield/cards/f219-lead-tickets-don-t-wait-on.md`. Write the tests first.
- In `runner/allowance.py`: `answer`, `_check`. `answer` keeps its answers for every other caller.
- In `runner/dispatch.py`: `_ticket_line`, `_claude_says` (queued rows keep it), and the module's docstring.
- In `runner/loop.py`: `_next_task`, `_waits_for_the_owner`, `at_reserve`, `_at_the_reserve`, `_week_switched_on`, `at_five_hour`, `_idle_line`, `claude_windows`, `rested_claude_windows`, `dry_run_plan`, `_dispatch_tickets`, `_stored_queue`, and `work_queue`'s docstring.
- `_next_task` tells a lead ticket by `task.agent`, the dry run by `router.lead_only`: use `router.lead_only` in both.
- Update `test_a_lead_ticket_short_of_the_reserve_runs_with_the_switch_off` and the tests of parking at the week's reserve in `tests/runner/test_loop.py`: they record the old rule. The 5-hour window's tests stay as they are.

### Done when
- `allowance.lead_hold` is tested for: under the line (no hold); 65% against 33% (a hold, naming the line); in the last 10% at 72% and at 95% (no hold), at 100% (a hold); past 75% of the 5-hour window (a hold); a window named in `reserves` (no hold)
- one test gives the runner and the dry run the same state and checks they choose the same next ticket, for each of: 65% against 33%, with a lead and a developer ticket (the developer's); the same with only the lead ticket (none, no park, no desk item); under the line (the lead's); 65% with the week's lever on (the lead's); 65% on a fast lane card (the lead's); the last 10% at 72% (the lead's); the 5-hour window at 80% with the week under its line (the developer's); a ticket parked for a limit, past its reset, at 65% (that ticket)
- at 65% against 33% a planner job, a review and a checkpoint still run
- the standing run's idle line says lead tickets wait for Claude's week, with until about when, and the run picks them up by itself once the line passes the reading
- an old `reserve` entry in `state.json` and its desk item are cleared at the start of a run
- a developer job on a cloud agent is still refused past its pace line (the existing router tests stay green)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

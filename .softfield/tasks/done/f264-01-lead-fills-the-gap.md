---
id: f264-01-lead-fills-the-gap
milestone: f264-the-factory-should-never-stay-idle
depends_on: []
agent: lead
difficulty: 4
area: factory
files:
  - runner/loop.py
  - runner/dispatch.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_dispatch.py
---

### Goal
Over Claude's week pace line or past its mark, when nothing else can start, the runner takes the next lead ticket in the board's order instead of standing idle; only Claude's real limit stops lead work (ADR 50).

### Context
Read "What happened", "Settled with the owner" and D1–D3 in `.softfield/cards/f264-the-factory-should-never-stay-idle.md` and `.softfield/adr/50-the-line-never-idles-for-the-pace.md`, then in `runner/allowance.py`: `lead_hold`, `lead_goes_at`, `_check`; in `runner/loop.py`: `_passing_over`, `_passed_over`, `choose_ticket`, `_lead_tickets_passed_over`, `_idle_line`; in `runner/dispatch.py`: `_ticket_line`. Tests to follow: `test_a_reviews_lead_fix_is_held_by_the_weeks_pace_line_as_any` (`tests/runner/test_loop.py`), `test_over_its_pace_line_a_lead_ticket_waits_and_names_the_line` and `test_at_the_weeks_reserve_a_lead_ticket_waits_and_support_jobs_may_use_it` (`tests/runner/test_dispatch.py`).
- `runner/allowance.py` doesn't change: D1 builds the question from `lead_hold` with `"seven_day"` in the reserves.
- The runner and the dry run must still choose through `choose_ticket` alone (ADR 44 item 9).
- `_held_at_the_limit` puts both `"seven_day"` and `"five_hour"` in the reserves (D1): past the 5-hour mark, too, developer tickets go first and a lead ticket fills the gap. The 5-hour park (`at_five_hour`) is removed by f264-03, not here: leave it as it is.
- Tests whose names or words say a lead ticket waits at the pace line or the reserve change with this rule: rename and rewrite them, don't delete what they check about developers and queued jobs.

### Done when
- with the week at 34% against a pace line of 26%, `choose_ticket` returns a free developer ticket when there is one, else the first free lead ticket in the board's order
- with the week at 80% (past its 70% mark) and no developer ticket free, it returns the first free lead ticket; at 100%, or with the week resting after a refusal, it returns None
- with the 5-hour window at 80% and the week under its line, `choose_ticket` returns a free developer ticket when there is one, else the first free lead ticket; at 100% of the 5-hour window it returns None
- under the line and the 5-hour mark, `choose_ticket`'s answers don't change (an existing test shows it)
- for the same state the dry run (`dry_run_plan`) names the same next ticket as the runner, at 34% and at 80% included
- the idle line names lead tickets as waiting for Claude only at 100% or a rest, with the reset; over the line, a lead row in the dry run says "goes when nothing else can (Claude's week over its pace)"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

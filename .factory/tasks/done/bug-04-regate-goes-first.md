---
id: bug-04-regate-goes-first
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 3
files:
  - runner/loop.py
  - runner/dispatch.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_dispatch.py
---

### Goal
A ticket whose finished attempt waits only for its gates (`state.regate`) is the runner's next job, so its gates run on the branch before main moves on and the work isn't thrown away.

### Context
Since `3671441`, `_recover` in `runner/loop.py` records an attempt that was stopped during its gates in `state.regate`, and `run_task` runs only its gates. On 2026-10-14 that never ran: f19-01's attempt 3 (57 min, its own `check-all` OK) waited five hours behind F22's review and five tickets. f14-03 and f14-04 changed `tests/factory_dashboard/test_planning.py` in the meantime, `_start_attempt` found a conflict and started a fresh branch, and a new attempt took 62 more minutes (job 878). Running the gates takes about 5 min (the suite on 16 workers, F71) and no model.
- Tickets are chosen in `_next_task` (`runner/loop.py`): parked tickets whose reset has passed go first, then the rest by `run_order`. Queued jobs (planner, escalation, direction, checkpoint, review) go before every ticket in `dispatch.plan` (`runner/dispatch.py`, `KINDS`, `_ticket_rank`), which is also the order the dashboard's queue shows.
- The new order: a planner job still goes first (the owner's answers, ADR 20); then a ticket in `state.regate`, before every other queued job and ticket; then everything as today. The ticket still needs its dependencies done and must not be paused or held: if it is, it waits as today.
- `dispatch.Ticket` gets a field saying its gates wait (the regate), set where `loop.py` builds the tickets for `dispatch.plan`; `_ticket_rank` puts it first and `plan` puts it right after the planner jobs. `_next_task` checks `state.regate` before the parked ones.
- A regate never needs Claude, so a Claude limit, the reserve or the 5-hour switch never holds it back.
- Follow the tests beside `_stopped_during_its_gates` in `tests/runner/test_loop.py`, and `plan`'s tests in `tests/runner/test_dispatch.py`.
- **Protected work: test-first.**

### Done when
- with a ticket in `state.regate`, a queued review and a ready ticket of better priority, the next pick is the regate ticket, and its gates run on the branch as it was left
- a queued planner job still goes before it
- a regate ticket whose dependency isn't done, or that is paused, waits as today
- while Claude is limited or at its reserve, the regate ticket is still picked
- `dispatch.plan` lists the regate ticket first after the planner jobs, so the dashboard's queue shows it next
- with nothing in `state.regate`, the order is unchanged (the existing order tests keep every assertion)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

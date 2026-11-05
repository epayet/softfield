---
id: bug-62-remove-week-reserve-park-leftovers
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
finding: f219-lead-tickets-don-t-wait-on-F4
files:
  - runner/owner.py
  - runner/requests.py
  - runner/state.py
tests:
  - tests/runner/test_owner.py
  - tests/runner/test_requests.py
---

### Goal
Nothing in the runner reads a ticket parked at the week's reserve any more, apart from the clean-up at the start of a run.

### Context
ADR 44 item 6 ended that park, and `open_session` removes an older run's entry, so these branches can no longer fire in a run. Keep a lapsed switch's own desk item (`RESERVE_KIND` with subject `week` or `five_hour`), and keep every 5-hour park.
- `runner/owner.py`: `_reserve_waits`, its loop in `owner_items`, and `"reserve"` in `_RERUN_KINDS`.
- `runner/requests.py`: `RESERVE_KIND` in `_free_parked`'s `held` and in `_settle_waits`; the week's `parked` kind in the switch request.
- `runner/state.py`: the comment on `parked` that still names "reserve".
- The tests in the listed files that build a `{"kind": "reserve"}` entry for a ticket go or move to the 5-hour park.

### Done when
- a search of `runner/` for a ticket's `reserve` park finds only `open_session` and `_resolve_reserve_parks`, which clear old ones
- a lapsed switch's desk item still opens and is still answered by turning the switch on
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

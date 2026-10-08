---
id: f31-01-settle-and-reject
milestone: f31-when-i-click-on-approve-plan
difficulty: 6
depends_on: []
agent: lead
files:
  - runner/planner.py
  - runner/requests.py
  - factory_dashboard/requests.py
  - factory_dashboard/planning.py
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_planning.py
priority: 0
---

### Goal
The runner takes a new `reject` request ("won't do"), and a rejected proposal counts as settled, so a thread whose proposals are all approved or rejected closes.

### Context
Read `docs/milestones/f31-when-i-click-on-approve-plan.md` D1, D2 and D3. The settling half of this ticket was built on 2026-10-08 by the lead in a terminal session: `proposal_state` in `runner/planner.py` (open, on its way, approved, sent back), `_close_if_settled`, `_settles` and `_settled` in `runner/requests.py` (a thread closes with a lead line and `archived_why` `approved` once every proposal of its latest set is settled), and the desk and thread reading `proposal_state` in `factory_dashboard/planning.py`. What is left:
- **`reject`** (D2): add `REJECT` beside the other kinds, to `_apply`, to `_COMMITS` (it may commit), and to `KINDS` in `factory_dashboard/requests.py`. Deleting the branch and removing the card follow `_drop_seed`'s steps (its commit, its thread line, its open planner rows, its item, `remove_cards`), for a card that isn't an idea too, as long as it has no ticket in `tasks/` and isn't building.
- `proposal_state` gains `rejected` (a worked `reject` on `<thread>/<id>`); `_settles` returns the thread for a worked `reject`, and `_close_if_settled` archives as `rejected` when every settled proposal was rejected, else `approved`, with the line "Rejected by the owner on <date>: won't do".
- **Protected work: test-first.**

### Done when
- `proposal_state` gives `rejected` for a worked `reject`, and a refused one leaves `open`
- `reject` on F7's plan, F7 an idea with no tickets: `plan/f7` is gone, F7's doc is removed in the commit "F7 rejected by the owner", the card leaves the board, and the thread is archived as `rejected`
- `reject` on a `replan` of a building card: the branch goes, the card and its tickets stay
- `reject` on a `merge` or a `seed`: nothing committed, only that proposal settled
- `reject` on a proposal not in the latest set, or already settled, is refused and changes nothing
- a thread with one proposal approved and the other rejected closes as `approved`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f31-01-settle-and-reject
milestone: f31-when-i-click-on-approve-plan
difficulty: 8
depends_on: []
agent: lead
files:
  - runner/planner.py
  - runner/requests.py
  - runner/metrics.py
  - factory_dashboard/requests.py
  - factory_dashboard/planning.py
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
The runner knows each proposal's state, archives a thread once the owner has settled every proposal of its latest set, and takes a new `reject` request ("won't do").

### Context
Read `docs/milestones/f31-when-i-click-on-approve-plan.md` D1, D2 and D3, and F6's D1 and D6 in `docs/milestones/f6-planning-room.md`. In `factory_dashboard/planning.py`: `_about`, `_settled`, `_open_proposals`, `_proposals` and `archived`. In `runner/requests.py`: `_apply`, `_approve_plan`, `_merged`, `_accept_adr`, `_plant` (a seed), `_drop_seed` and `_archive`. In `runner/metrics.py`: `latest_proposals`, `set_thread_archived` and the `ALTER TABLE planner_threads ADD COLUMN archived` migration.
- Move `_about` and `_settled` into `runner/planner.py` as one public `proposal_state(proposal, card, requests)` that returns `open`, `on its way`, `approved`, `rejected` or `sent back` (D3). The dashboard's desk and thread read it, so their behaviour stays as it is today; the page's words change in f31-02.
- A worked request settles a proposal only when it is about that proposal, by `_about`'s rules plus `reject` on `<thread>/<id>`. A refused one leaves it open, as today.
- **Settling:** after a request about a proposal worked (in `apply_requests`, once its result is stored), when every proposal of the thread's latest set is settled, add the lead line and archive with the reason (D1). Store the reason beside `archived` (a new `archived_why` column, `approved` or `rejected`; the owner's own archive is `by you`). The Archived list says it: "approved · archived 3 min ago".
- **`reject`** (D2): add `REJECT` beside the other kinds, to `_apply`, to `_COMMITS` (it may commit), and to `KINDS` in `factory_dashboard/requests.py`. Deleting the branch and removing the card follow `_drop_seed`'s steps (its commit, its thread line, its open planner rows, its item, `remove_cards`), for a card that isn't an idea too, as long as it has no ticket in `tasks/` and isn't building.
- **Protected work: test-first.**

### Done when
- `proposal_state` gives each of the five states, a refused request leaving `open`, and a request made before the lead's message not counting
- approving the only `plan` of F7's latest set archives F7's thread as `approved`, adds the line "Approved by the owner on <date>: <the approval's result>", and resolves its `planning` item; the desk no longer lists it
- accepting F7's ADR while its plan is open leaves the thread on the desk; approving the plan afterwards archives it
- a thread whose latest set has one `plan` approved and one `merge` untouched stays on the desk
- `reject` on F7's plan, F7 an idea with no tickets: `plan/f7` is gone, F7's doc is removed in the commit "F7 rejected by the owner", the card leaves the board, and the thread is archived as `rejected`
- `reject` on a `replan` of a building card: the branch goes, the card and its tickets stay
- `reject` on a `merge` or a `seed`: nothing committed, only that proposal settled
- `reject` on a proposal not in the latest set, or already settled, is refused and changes nothing
- the owner's message on an archived thread opens it again and clears its reason
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

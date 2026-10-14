---
id: f75-01-archiving-on-approval
milestone: f75-i-believe-right-now-when-a
difficulty: 3
depends_on: [f74-01-one-box-per-conversation, f22-01-archive-at-the-bottom]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A thread whose last open proposal the owner just approved or rejected shows at once as archiving (dashed orange, "archiving at the runner's next pick"), on the desk and on its page, as a manual Archive does.

### Context
Read `.factory/cards/f75-i-believe-right-now-when-a.md` (Why it happens, D1–D4), then `_close_if_settled`, `_settled` and `_latest` in `runner/requests.py` (the runner's rule), and `_open_proposals`, `_gone_merge`, `_acted_on` and `thread_page` in `factory_dashboard/planning.py`.
- Add one helper in `factory_dashboard/planning.py`, say `_closing(conn, project_id, card, known) -> bool`: the latest lead message of the thread that lists proposals, the owner's requests since it, then D1: every proposal is `APPROVED`, `REJECTED`, `ON_ITS_WAY` (from `proposal_state`) or `_gone_merge`, and at least one is `ON_ITS_WAY`. An archived thread, or one with no proposals, is never closing.
- D2: a pending `reject` whose subject is `<card>/<id>` of a proposal whose kind is in `DRAFTED` (`runner/planner.py`) makes every `DRAFTED` proposal of that set count as on its way.
- `_acted_on` also dashes a thread's own item (not its `/proposals/` items, which are already dashed) when `_closing` holds, with the words "archiving at the runner's next pick".
- `thread_page`: when `_closing` holds and no archive request is pending, `archiving` is `"on"`, so `factory_dashboard/templates/thread.html` shows its existing "Archiving at the runner's next pick" mark and hides the Archive button as for a manual archive.
- Use `_known_cards(_repo(conn, project))` for `known`, as `thread_page` does for `_proposals`.

### Done when
- a thread whose latest set is one `plan` with a pending `approve_plan` for the card: its `answers` item is dashed (`on-its-way-item`) with "archiving at the runner's next pick", and it is not in `waiting_for_you`
- the same with a pending `reject` on the plan instead: same dashed item
- a set of a `plan` and an `adr`, pending `approve_plan` only: the thread's item stays solid and counted
- a set of a `plan` and an `adr`, pending `reject` on the plan: the thread's item is dashed (D2)
- a set with one proposal already approved and another with a pending approval: dashed
- a refused approval (done, result not in `WORKED`): the thread's item is solid again
- `/planning/<card>` for a closing thread shows "Archiving at the runner's next pick" and no Archive button
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

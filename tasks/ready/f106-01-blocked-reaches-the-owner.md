---
id: f106-01-blocked-reaches-the-owner
milestone: f106-where-do-blocked-tickets-go-for
difficulty: 6
depends_on: []
agent: lead
files:
  - runner/loop.py
  - runner/requests.py
  - runner/owner.py
  - factory_dashboard/requests.py
  - docs/workflow.md
  - docs/task-format.md
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_requests.py
---

### Goal
The runner tells the owner the moment it blocks a ticket, and two requests take a blocked ticket out of `tasks/blocked/`: try it again, or set it aside.

### Context
Read `docs/milestones/f106-where-do-blocked-tickets-go-for.md` (D1, D3), then `block`, `waiting_behind`, `move_to_ready` and `run_lead_task` in `runner/loop.py`, `owner_items` and `_RERUN_KINDS` in `runner/owner.py`, `_apply`, `_COMMITS` and `_switch` (how a request resolves owner items) in `runner/requests.py`, and `KINDS` in `factory_dashboard/requests.py`. `runner/**` is protected: write the tests first, each failing for the right reason.
- **The item:** `block` stores an owner item of kind `blocked`, subject the ticket's id, text "<id> blocked: <reason>" plus " · N tickets wait behind it" when some do. The verdict in `runner/owner.py` writes the same words, so a rerun doesn't change them. No command on the item: the desk has buttons.
- **Try again:** a `queue` request also takes a ticket from `tasks/blocked/` (later/ first, as today). Before the move, the branch `task/<id>`, when it exists, is copied to `blocked/<id>` (replacing an older copy): a lead ticket starts again from main (`run_lead_task` resets its branch) and the failed work must not be lost.
- **Set aside:** a new request kind, set_aside, subject the ticket's id, moves it from `tasks/blocked/` to `tasks/later/` in a commit of its own, as `move_to_ready` commits. It names a ticket in blocked/ only; anything else is refused with a plain reason.
- Both resolve the ticket's open `blocked` item. The dashboard accepts the new kind.
- The ticket keeps its runner footers.

### Done when
- a lead ticket whose check-all fails: an open `blocked` item exists for it right after, with its reason, and with the count of ready tickets that depend on it when there are some
- a `queue` request for a blocked ticket: it is in `tasks/ready/`, committed alone, its item resolved, and `blocked/<id>` holds what `task/<id>` held
- a `queue` request for a ticket in later/ works as before
- a set_aside request for a blocked ticket: it is in `tasks/later/`, committed alone, its item resolved; for a ticket in ready/, done/ or unknown, and for an empty subject, it is refused and nothing moves
- `POST /requests` takes the new kind
- `docs/workflow.md` and `docs/task-format.md` say how a blocked ticket comes back
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

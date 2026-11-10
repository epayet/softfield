---
id: f231-02-drop-a-set-aside-ticket
milestone: f231-there-are-many-bugs-in-the
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/requests.py
  - factory_dashboard/requests.py
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_requests.py
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_requests.py
---

### Goal
The owner can remove a set-aside ticket from the dashboard: a `drop_ticket` request the runner applies at its next pick.

### Context
Read D1 and D2 in `.softfield/cards/f231-there-are-many-bugs-in-the.md`, `def _drop_seed` and `def _apply` in `runner/requests.py` (the worked example), and `def remove_missing_tickets` in `runner/metrics.py`. `runner/**` is protected: tests first.
- `DROP_TICKET = "drop_ticket"` beside `DROP_SEED`, in `_COMMITS` (it commits on main, so it waits for main as a queue does), and in `KINDS` in `factory_dashboard/requests.py`.
- Applied: the ticket's file `git rm`ed from `.softfield/tasks/later/` in a commit of its own, `<id> removed by the owner`, with the runner's author and trailers as `_drop_seed` writes them; its row marked `removed` at once, so the board doesn't wait for the next sync. Result: `removed .softfield/tasks/later/<id>.md`.
- Refused, main unchanged: an empty subject, or a ticket that isn't in `.softfield/tasks/later/` (`<id> is not set aside: not removed`). A git failure puts the file back, as `_drop_seed` does.

### Done when
- a `drop_ticket` for a ticket in `.softfield/tasks/later/` removes its file in one commit, and its row reads `removed`
- one for a ticket in ready/, blocked/ or done/, or for no ticket, is refused and main is unchanged
- one sent while the repo is off main waits, as a queue does
- `POST /requests` with `kind=drop_ticket` writes the row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

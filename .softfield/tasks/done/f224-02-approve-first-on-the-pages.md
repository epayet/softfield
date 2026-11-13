---
id: f224-02-approve-first-on-the-pages
milestone: f224-i-want-to-be-able-to-2
difficulty: 3
depends_on: [f224-01-approve-first-in-the-runner]
files:
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/board.html
  - factory_dashboard/board.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_proposal.py
  - tests/factory_dashboard/test_board.py
---

### Goal
A review page offers Approve first in a fold, and an approval pressed that way shows at once on the board and the Overview.

### Context
Read `.softfield/cards/f224-i-want-to-be-able-to-2.md` (D1, D5, D6). The picture to build is `.softfield/cards/f224-mockup/approve-first.html`.
- `factory_dashboard/templates/proposal.html`: `#approve-plan` is the request to copy, with `"value": "first"` added. `details#reject` is the fold to follow, and the page's script hides `#primary` while a comment is written.
- `factory_dashboard/static/dashboard.css`: the phone's dock rules for `#reject` (one 44 px row, an open fold on a row of its own), `.btn.go`, `.card-reserve`.
- `factory_dashboard/board.py`: `lane_requests` reads the open `reserve` requests, `Card.lane_asked` holds them, `reserve_marked` feeds the Overview. Follow `tests/factory_dashboard/test_board.py`'s "a card with an open fast lane request" tests.

### Done when
- on a plan, mock-up or replan with `open` state: `details#approve-first` sits between `#primary` and `#reject`, closed, its summary "Approve first…" at 1280 px and "First…" at 390 px, and its button posts `kind=approve_plan`, `value=first`
- it isn't on an ADR, a merge or a seed; with `adr_waits` its button is disabled as Approve plan is
- its text says the card goes first, into the fast lane, ahead of every other job, and may use Claude's reserve, as the mock-up does
- pressing it marks `#actions` on its way, as Approve plan does; while a comment is written the fold is hidden with `#primary`
- at 390 px, in a browser, the closed dock is one row and fits without scrolling sideways; an open fold takes a row of its own
- with such a request open, the card shows "goes first · fast lane · on its way · at the runner's next pick" in dashes, in whichever stage it stands, and the Overview's Fast lane line names it; once the request is done both go back to what the card's doc says
- a plain open approval changes nothing on the board
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 1027098
logs: .softfield/var/runs/20261112-170349/f224-02-approve-first-on-the-pages
```

```yaml
# --- runner ---
result: done
finished_by: lead
```

---
id: f5-15-board-data
milestone: f5-board
depends_on: [f5-07-replan]
difficulty: 5
files:
  - factory_dashboard/board.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
`factory_dashboard/board.py` turns the database into the board's cards: every milestone and every bug ticket, in its growth stage, in priority order, with what the page shows on each card.

### Context
Read `docs/adr/19-feature-board.md` (items 1–4), `docs/milestones/f5-board.md` (D4–D6), the board mock-up (`docs/milestones/f5-board-mockup/Main.dc.html`, `docs/milestones/f5-board-mockup/Phone.dc.html`, `docs/milestones/f5-board-mockup/Card.dc.html`: read the markup and the data in each file's script, not a page to open), and `factory_dashboard/overview.py` (how the Overview reads milestones, tickets and running jobs; the worked example for a page's data).
- **Stages, in order:** seed, sprouting, planted, growing, ripe, harvested.
  - A milestone's stage comes from its `state`: idea → seed, planning → sprouting, ready → planted, building → growing, needs sign-off → ripe, done → harvested.
  - A bug ticket's stage (ADR 19 item 2):
    - `later` → seed (with the note "ticket written, set aside");
    - `ready` → planted;
    - a running job, or `running` → growing;
    - `done` → harvested.
- **Each card:** key (or the bug's ticket id), title, area, whether it's a bug, priority, tickets done of total and how many set aside (milestones), and for a growing card what runs now (ticket, goal, agent, attempt). Cards in a stage are sorted by priority, then key.
- `board(conn, project, q=None, kind=None) -> Board`:
  - `q` keeps cards whose key or title contains it, case-insensitive;
  - `kind` is `factory`, `product` or `bug`;
  - harvested keeps only the latest 4 (by `milestones.ended` or the merge time), with how many more there are.
- Plain dataclasses; no HTML here. Put your fixture rows in your own function in `tests/factory_dashboard/conftest.py`.

### Done when
- a milestone with state idea is a seed; one building with 3 of 17 tickets done shows "3 of 17" and its running ticket
- a bug ticket in `later` is a seed card marked as a bug, with its area; once `ready` it's planted
- cards within a stage come in priority order
- `q="duck"` keeps only matching cards; `kind="bug"` only bugs
- with 6 harvested milestones, 4 are kept and "2 more" is reported
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f5-15-board-data
milestone: f5-board
depends_on: [f5-07-replan]
agent: lead
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
Read `docs/adr/19-feature-board.md` (items 1–4), `docs/milestones/f5-board.md` (D4–D6), the board mock-up (`docs/milestones/f5-board-mockup/Main.dc.html`, `docs/milestones/f5-board-mockup/Phone.dc.html`, `docs/milestones/f5-board-mockup/Card.dc.html`: read the markup and the data in each file's script, not a page to open), `_field` in `factory_dashboard/line.py` (the same rule, for the line's field) and `factory_dashboard/overview.py` (`running_jobs`).
- **Stages, in order:** seed, sprouting, planted, growing, ripe, harvested.
- **A milestone's stage** (D4: derived from its thread and its tickets; nothing writes `planning`, `building` or `needs sign-off` into a doc as work goes on). The first that holds:
  1. `milestones.status` is `done` (the sign-off sets it, with `ended`) → harvested;
  2. `milestones.state` is `idea` and no planning thread is about the card (`planner_threads.card` is its short key; `_seeds` in `factory_dashboard/planning.py`) → seed; state `planning`, or an idea with a thread → sprouting;
  3. every ticket done and the review's sheet stored (`milestones.signoff`) → ripe, as `_field` has it;
  4. a ticket has started (a job on one of its tickets, or a ticket `running`, `done`, `escalated` or `blocked`) → growing;
  5. otherwise → planted (state `ready`, or tickets all still `ready`).

  A ticket in `later` or `removed` counts for none of these.
- **Left out:** a milestone whose `state` is `removed` (`metrics.REMOVED`: its doc left the repo), a ticket whose state is `removed`, and the `bugs` row itself (a standing key, not a card).
- **A bug ticket's stage** (ADR 19 item 2), from `tickets.state` (its folder, or `running`), for the tickets of the `bugs` milestone:
  - `later` → seed (with the note "ticket written, set aside");
  - `ready` → planted;
  - `running`, a running job, `escalated` or `blocked` → growing;
  - `done` → harvested.
- **Each card:** key (the short key in capitals, `F5`; or the bug's ticket id), the full key for its link, title, area, whether it's a bug, priority, tickets done of total and how many set aside (milestones; set-aside ones aren't in the total), and for a growing card what runs now (ticket, goal, agent, attempt; `running_jobs`, live ones only). Cards in a stage are sorted by priority, then key.
  - A milestone's priority and area are `milestones.priority` and `milestones.area`; a row the runner made before reading its doc has neither: 100, and the area of its series (`f` factory, `m` product), as `card` in `runner/milestone.py` has them.
  - A bug's area is `tickets.area`; its priority is what `ticket_priority` in `factory_dashboard/queries.py` reads (its own `priority:`, else 50).
- `board(conn, project, now, q=None, kind=None) -> Board`:
  - `q` keeps cards whose key or title contains it, case-insensitive;
  - `kind` is `factory`, `product` or `bug`;
  - harvested keeps only the latest 4, with how many more there are: by `milestones.ended`, and for a bug by its latest job's `ended` (a ticket row has no merge time).
- Plain dataclasses; no HTML here. The fixture rows go in a function of their own in `tests/factory_dashboard/conftest.py`.

### Done when
- a milestone with state idea is a seed, and sprouting once a planning thread is about it; one whose state says ready with a ticket merged is growing, and shows "1 of 3" and its running ticket
- a milestone with every ticket done is growing until its review's sheet is stored, then ripe, then harvested once signed off
- a removed card, a removed ticket and the `bugs` row make no card
- a bug ticket in `later` is a seed card marked as a bug, with its area; once `ready` it's planted
- cards within a stage come in priority order
- `q="duck"` keeps only matching cards; `kind="bug"` only bugs
- with 6 harvested milestones, 4 are kept and "2 more" is reported
- for the fixture, the ripe cards are the line's field's ripe ones (`live_line`), and the harvested ones its stash
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

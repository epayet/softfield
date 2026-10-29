---
id: f172-06-next-in-line-marked-first
milestone: f172-i-d-like-to-be-able
difficulty: 3
depends_on: [f172-04-marked-tickets-go-first, f172-05-reserve-lever-on-the-milestone-page]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Next in line shows the fast lane on top: the tickets of cards in the fast lane, in a striped bay headed "Fast lane", above the queued planning, direction, checkpoint and review jobs, as the runner now picks them.

### Context
The picture to build is `.factory/cards/f172-mockup/goes-first.html` (Proposed, "Next in line"). Read D7 and D9 in `.factory/cards/f172-i-d-like-to-be-able.md`.
- Next in line is `factory_dashboard/templates/_partials/queue.html`: the queued jobs (`queued_jobs`, from `queued_jobs` in `factory_dashboard/overview.py`, ordered by `dispatch.plan`), then the tickets (`next`). Find where `next` is built in `factory_dashboard/overview.py`.
- The lane's cards come from `board.reserve_marked` (already in the Overview's context as `reserve_cards`). A ticket goes in the bay when its card is in the lane; a ready ticket it waits for goes there too (as `loop.reserve_cards` does in the runner). Keep the runner's order inside the bay; each row names its card.
- Pass the lane's ticket ids to `dispatch.plan` as `first`, which f172-04 added, so a direction or escalation of a lane ticket sits in the bay with it.
- The bay uses the hazard stripe and the ink, as `.card-reserve` does (`factory_dashboard/static/dashboard.css`): ornament never takes a status colour.

### Done when
- with F142 in the lane and planner jobs queued, F142's ready ticket is the first row of Next in line, inside the "Fast lane" bay
- a queued direction for a lane ticket shows inside the bay
- with no card in the lane, Next in line is as today, with no bay
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

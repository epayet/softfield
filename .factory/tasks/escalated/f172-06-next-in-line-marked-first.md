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
The picture to build is `.factory/cards/f172-mockup/goes-first.html` (Proposed, "Next in line", its `.lane-bay`). Read D7 and D9 in `.factory/cards/f172-i-d-like-to-be-able.md`.
- Next in line is `factory_dashboard/templates/_partials/queue.html`: first the queued jobs (`queued_jobs`, from `queued_jobs` in `factory_dashboard/overview.py`, ordered by `dispatch.plan`), then the tickets (`next`).
- `next` is set in `_live_context` in `factory_dashboard/overview.py` to the first three rows of `live_line(...)["queue"]`, which `factory_dashboard/line.py` builds (don't edit line.py). Each row is a dict with `ticket`, `milestone` (the full key) and `waits` (the dependencies it still waits for). Split the whole queue in `_live_context`.
- The lane's cards come from `board.reserve_marked`, which is already in the Overview's context as `reserve_cards`. Each is a `Card` whose `key` is the short key in capitals. A ticket goes in the bay when its card is in the lane, and so does a ready ticket that a lane ticket waits for (as `loop.reserve_cards` does in the runner). Keep the runner's order inside the bay, and have each row name its card.
- Pass the lane's ticket ids to `dispatch.plan` as `first`, which f172-04 added, so that a direction or escalation of a lane ticket sits in the bay with it.
- The bay uses the hazard stripe and the ink, as `.card-reserve` does (`factory_dashboard/static/dashboard.css`). Ornament never takes a status colour.
- Tests: `_reserve_client(board_db, tmp_path, "f23-planted")` in `tests/factory_dashboard/test_overview.py` marks F23, whose `f23-01-first` and `f23-02-second` are ready in `board_db`. Queue jobs with `metrics.queue_job` as the existing checkpoint test does.

### Done when
- with F23 in the lane and a planner job queued, F23's first ready ticket is the first ticket row of Next in line, inside the "Fast lane" bay, and the planner job is outside it, below
- a queued direction for `f23-01-first` shows inside the bay, before the lane's tickets
- with no card in the lane, Next in line is as today, with no bay
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 213228
logs: .factory/var/runs/20261029-143524/f172-06-next-in-line-marked-first
```

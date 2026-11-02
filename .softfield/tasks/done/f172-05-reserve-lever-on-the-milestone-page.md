---
id: f172-05-reserve-lever-on-the-milestone-page
milestone: f172-i-d-like-to-be-able
difficulty: 3
depends_on: [f172-07-fast-lane-in-the-card]
files:
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/planning.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The fast lane lever is on the card's page you reach from the board (`/milestones/<key>`), as a "Fast lane" row of its header, and no longer on the planning thread's page; the board and the Overview say "fast lane".

### Context
The picture to build is `.softfield/cards/f172-mockup/goes-first.html` (Proposed: "The card's page", "The board" and "The Overview"). Read D8 in `.softfield/cards/f172-i-d-like-to-be-able.md`.
- Today's lever is in `factory_dashboard/templates/thread.html` (`#reserve-bay`), built by `_reserve_lever` and `ReserveLever` in `factory_dashboard/planning.py`. Move both to `factory_dashboard/milestones.py`, where the milestone page's context is built, and the markup into `#card-head`'s `dl` in `factory_dashboard/templates/milestone.html` as `<dt>Fast lane</dt><dd>…</dd>` after Tickets. The request it posts stays the same (`kind: "reserve"`, the card's short key, `on` or `off`).
- The row shows only when `_reserve_lever` returns a lever, as today: a planted card with tickets left.
- The lever reads "fast lane"; under it one short line: "Goes before everything, planning and reviews too, and uses both of Claude's reserves. Leaves the lane when its tickets are done." The `.reserve-bay` CSS in `factory_dashboard/static/dashboard.css` can go if nothing else uses it; the `.lever` CSS stays.
- The board's plate (`factory_dashboard/templates/board.html`, `.card-reserve`) reads "fast lane".
- In `factory_dashboard/templates/_partials/allowance.html`, the line under Claude's meters reads "Fast lane:" instead of "Past both marks for:", and its links go to `/milestones/<full key>`; `board.reserve_marked` gives each card's `full_key`.
- Python names (`reserve`, `reserve_marked`, `ReserveLever`) may stay: only what a page shows changes.

### Done when
- a planted card's `/milestones/<key>` page shows the Fast lane row with the lever, off or on as its doc says, and a lever asked for shows on its way
- an idea, a done card, or a planted card with every ticket done shows no Fast lane row
- the planning thread's page shows no lever
- a card in the lane shows "fast lane" on the board, and the Overview lists it after "Fast lane:", linking to its `/milestones/` page
- no page says "may use Claude's reserve", "uses Claude's reserve" or "Past both marks for"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 392874
logs: .softfield/var/runs/20261029-110520/f172-05-reserve-lever-on-the-milestone-page
```

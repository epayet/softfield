---
id: f28-02-now-shows-resuming-without-a-button
milestone: f28-the-first-time-i-clicked-on
difficulty: 2
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Overview's Now shows the owner's pause in the same words as the top bar, "Resuming…" included, and drops its own Pause/Resume button.

### Context
Read `factory_dashboard/templates/_partials/running.html` (its last block, f5-18) and `pausing` in `factory_dashboard/overview.py`.
- The owner (F29, 2026-10-07): "the top was saying 'resuming' but in the overview page the resume button was still available".
- The top bar's words come from `factory_status` in `factory_dashboard/app.py`: paused and a resume asked is "Resuming…"; paused is "Paused by you since HH:MM"; a pause asked is "Pausing after this job". Now shows the same three, from the same requests (`_asked` in `factory_dashboard/app.py`).
- D3: the top bar, on every page, is the one Pause/Resume. Remove both buttons from Now; with no pause held or asked, Now shows no pause line.
- `tests/factory_dashboard/test_requests.py` checks "Pausing after this job" in Now; keep it passing.

### Done when
- paused with a resume asked: Now shows "Resuming…" and no Resume button
- paused: "Paused by you since HH:MM"; a pause asked: "Pausing after this job"; neither has a button
- nothing asked or held: no pause line and no Pause button in Now
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

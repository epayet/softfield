---
id: f188-01-count-leaves-the-phone-bar
milestone: f188-i-don-t-need-the-4agreef
difficulty: 1
files:
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_thread.py
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
On a phone, the bar that stays at the bottom of a review page no longer shows "N agreed · M to change": it holds the button and the closed Reject… fold only. On a wide screen the count stays.

### Context
The picture to build is `.factory/cards/f188-mockup/review-dock.html` (Proposed).
- The count is `#review-count` in `factory_dashboard/templates/proposal.html`; its script updates it as comments are written. Leave the template and the script as they are: hide it in the phone rules (`@media (max-width: 639px)`, the "f42" block) of `factory_dashboard/static/dashboard.css`, and drop the rule there that sizes it.
- With the count gone, the button sits at the left of the bar and the closed Reject… fold at the right edge, as in the mock-up; an opened fold still takes a row of its own.
- `test_the_dock_is_compact_on_a_phone` in `tests/factory_dashboard/test_thread.py` checks the count is in the bar's row: it now checks the count is not visible at 390 px and the row holds `#approve-plan` and `#reject > summary`.
- The dashboard is English only: no translation needed.

### Done when
- at 390 × 844 on a review page, `#review-count` is not visible, the bar is at most 72 px tall, and the button and the closed Reject… fold sit on its one row, the fold to the right of the button
- with a comment written at 390 px, the bar shows "Send 1 change back" and still no count
- at a wide screen, the count still shows and still updates as comments are written
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

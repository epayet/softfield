---
id: f123-01-projects-drag
milestone: f123-projects-page-drag-to-reorder
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/projects.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
The Projects page's rows take the look they will have once they can be dragged: each project a plate with its place, and an order on its way shown on every row, with nothing locked. The script that drags comes next (f123-02).

### Context
Read `.factory/cards/f123-projects-page-drag-to-reorder.md` (D1, D4). The picture to build: `.factory/cards/f123-mockup/projects-drag.html` (its Proposed, without the grip and ⋯, which f123-02's script adds as the board's script does).
- Today's page: `#projects-order` in `factory_dashboard/templates/projects.html`; `factory_dashboard/projects.py` passes `cards` (in the order sent when one waits) and `asked`. That Python file doesn't change.
- Each row (`li.proj`) gets `data-key` (its name, beside `data-name`) and shows its place as `#1`, `#2`… in the display font, in the hazard ink, beside its name: the plate of the mock-up, on the tokens in the Projects page's block of `factory_dashboard/static/dashboard.css`.
- When `asked` is true every row reads "on its way · at the runner's next pick" (the board's `.card-way` look) with the board's dashed hazard edge, in place of today's `--opus` one, and its number box is no longer disabled: sending again replaces the order on its way (D4).
- Keep the number boxes and the inline script working for now: f123-02 replaces them.

### Done when
- every project row has `data-key` its name and shows its place `#1`, `#2`… in the order shown
- with a `project_order` waiting, the rows are in the order sent, each reads "on its way · at the runner's next pick", and no input is disabled
- with none waiting, no row says "on its way"
- `test_the_projects_page_lays_out_at_phone_and_display_sizes` still passes at both sizes
- `test_an_order_not_taken_yet_shows_as_sent_and_cant_be_edited` is replaced by a test of the above
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

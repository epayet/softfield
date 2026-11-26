---
id: f300-02-fix-button-shows-its-card
milestone: f300-the-factory-project-page-shouldn-t
difficulty: 2
depends_on: [f300-01-stack-plate-shows-its-card]
files:
  - factory_dashboard/stacks_routes.py
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/templates/_partials/app_row.html
tests:
  - tests/factory_dashboard/test_projects.py
  - tests/factory_dashboard/test_stacks_routes.py
---

### Goal
A crashed app, or one whose update failed, whose fix the owner already asked for shows that request in its row instead of "Plant and ask the lead to fix it", and leaves Needs you.

### Context
The picture to build is the wardrobe-teller plate and the missing Needs you panel on the Proposed side of `.softfield/cards/f300-mockup/projects-asked.html`. Read D2–D5 in `.softfield/cards/f300-the-factory-project-page-shouldn-t.md`; then `asked_card` and `AskedCard` (f300-01), `fix_text`, `row_of`, `app_row` and `AppRow` in `factory_dashboard/stacks_routes.py`, the Needs you list in `factory_dashboard/projects.py` and `factory_dashboard/templates/projects.html`, and `factory_dashboard/templates/_partials/app_row.html`.
- `AppRow.asked: AskedCard | None`, filled by `row_of` only for a broken app, with `text_start = f"{name}'s app "`. `row_of` takes the connection as its first argument; update every caller (`project_cards`, the Run and Stop routes, and the `GET /projects/{name}/app` route if it exists).
- `app_row.html`: with `row.asked`, the on-its-way line or the `.order` link from f300-01 in place of the fix button; Run and Logs stay, and so do the red lamp and word.
- Needs you: a broken app's line only when `not card.app.asked`, and `needs_you_count` counts the same lines.

### Done when
- a crashed app with a live fix card shows the card's key, title and state in its row, no fix button, and no line in Needs you
- a crashed app with an open fix plant shows the on-its-way line and no fix button
- a crashed app with no fix asked, or whose fix card is done, shows the button and its Needs you line as today
- `test_the_projects_page_lays_out_at_phone_and_display_sizes` still passes at both sizes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

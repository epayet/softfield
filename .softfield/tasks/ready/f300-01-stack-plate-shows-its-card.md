---
id: f300-01-stack-plate-shows-its-card
milestone: f300-the-factory-project-page-shouldn-t
difficulty: 2
depends_on: []
files:
  - factory_dashboard/stacks_routes.py
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
A project without a stack whose stack the owner already asked for shows that request on its plate (on its way, or the card it became) instead of "Plant and ask the lead for a stack".

### Context
The picture to build is the coaster-ranker and coucou plates on the Proposed side of `.softfield/cards/f300-mockup/projects-asked.html`. Read D1–D4, D6 and D7 in `.softfield/cards/f300-the-factory-project-page-shouldn-t.md`; then `STACK_PLANT`, `plant_value` and `AppRow` in `factory_dashboard/stacks_routes.py`, `ProjectCard` and `project_cards` in `factory_dashboard/projects.py`, the `stack_plant` branch of `factory_dashboard/templates/projects.html`, and the results `_plant` writes in `runner/requests.py` ("planted …").
- Add `AskedCard` and `asked_card` to `stacks_routes.py` as D2 says; `short_key` is in `runner/tasks.py`.
- `ProjectCard.stack_asked: AskedCard | None`, filled in `project_cards` only when `stack_plant` is set.
- In `projects.html`, the stack row: with `stack_asked` on its way, the row gets the dashed on-its-way edge and the D4 line, no button; with a card, "No stack yet." and the work order link (`.order`) as drawn; with None, today's row unchanged.
- CSS for `.order` and the on-its-way row goes in the app row's block of `factory_dashboard/static/dashboard.css`, on existing tokens only.
- Tests seed `owner_requests` and `milestones` rows as the existing Projects page tests do.

### Done when
- a project with a done stack plant whose card is `ready` shows "You asked the lead", the card's key, title and "ready", linking to `/planning/<short key>?project=<name>`, and no plant button
- a project with an open stack plant shows the on-its-way line and no button
- a project whose stack card is `done` or `removed`, or that was never asked, shows the button as today
- `test_the_projects_page_lays_out_at_phone_and_display_sizes` still passes at both sizes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

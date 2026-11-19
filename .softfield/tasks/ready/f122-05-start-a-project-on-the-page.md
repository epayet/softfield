---
id: f122-05-start-a-project-on-the-page
milestone: f122-new-project-from-the-projects-page
difficulty: 5
depends_on: [f122-04-replan]
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
The Projects page has a "Start a project" panel; a sent project's plate shows at once as on its way, and a project being set up shows where its setup is, with a link to its first card.

### Context
The picture to build is `.softfield/cards/f122-mockup/projects-new.html` (Proposed). Read D6 in `.softfield/cards/f122-new-project-from-the-projects-page.md` and its Replan section, then `project_cards` and `projects_page` in `factory_dashboard/projects.py`, and `factory_dashboard/templates/projects.html`.
- The panel posts to `/requests` with htmx as the order form on the same page does: `kind=new_project`, `project` the page's own `project` field (the handler ignores it), `value` the JSON of D2 (`name`, `idea`, `built_with`, `app`, which is ticked by default; `"on"` counts as ticked, and an empty name or built-with is fine). "Goes in" shows `projects_root()` from `runner/config.py` plus the name as typed, updated as the owner types.
- A waiting `new_project` request (an `owner_requests` row of kind `runner.requests.NEW_PROJECT` with `done` null, read as `order_on_its_way` reads the order's) draws a plate at the end of the list from its own value: the name, the idea cut to two lines, the first station lit, the dashed orange `.way` edge, and "On its way: the runner makes its folder at its next pick". It isn't editable and has no place number to change. Once the runner takes the request the project's own plate replaces it, with no gap.
- A project paused `setting up` (`ProjectCard.paused == metrics.SETTING_UP`) shows the line of four stations: "Set up by the lead" lit while an open `work_queue` row of kind `dispatch.SETUP` exists for it (`metrics.open_jobs`), "ADR 00 for you" while its `for_you` is above zero, and "Answer on its first card" linking to `/planning/m1?project=<name>`, instead of Board and Overview.
- The stations are drawn in CSS from the tokens at the top of `factory_dashboard/static/dashboard.css`; the lit one uses the hazard colour, never `--good` or `--fail`, and nothing blinks.
- The line "A new project is set up on its computer…" goes.

### Done when
- the page shows the panel with the idea, name, built with and app fields and the folder it goes in
- a waiting `new_project` request shows its plate, on its way, with the owner's name and words
- a setting-up project shows the right lit station for: a setup job waiting, ADR 00 waiting; and the link to M1's thread
- a live project's plate is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

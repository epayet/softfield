---
id: f132-08-picker-in-the-tabs
milestone: f132-the-overview-shows-the-whole-factory
difficulty: 2
depends_on: [f132-02-overview-live-every-project]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The project picker sits in the tab strip in front of the three pages it changes (Planning, Board, Tickets), drawn with them as one bay, and a factory-wide page's crumbs start "The whole factory".

### Context
Read `.softfield/cards/f132-the-overview-shows-the-whole-factory.md` (D2, D7) and build the Proposed top bar of `.softfield/cards/f132-mockup/overview.html` (`.bay-group`).
- `factory_dashboard/templates/base.html`: the `filters` form in `.bar-top`, the `nav.tabs` loop and the crumbs; `factory_dashboard/static/dashboard.css`: `nav.tabs` and `.filters`.
- The tab order stays: Projects, Overview, then the bay (the picker, Planning, Board, Tickets), then Jobs, Runs, Timeline, Agents, Bench. The bay uses the existing tokens only (the rule, the plate, the hazard stripe faint), never a status colour.
- The form still submits on change and keeps its `<noscript>` button; the Planning tab keeps its `id="planning-tab"` (the live poll swaps its count).
- The factory-wide pages are D2's list; their crumbs start "The whole factory", a project's pages keep the project's name.
- On a phone the tabs still wrap, and the active tab still scrolls into view.

### Done when
- every page's tab strip has the picker right before Planning, and the bar's top row has no picker
- choosing a project in the picker reloads the page with that project, as today
- the Overview's crumbs read "The whole factory"; the Board's start with the project's name
- one project only: the picker still shows, with its one name
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

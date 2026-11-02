---
id: f193-01-picker-in-project-order
milestone: f193-the-project-picker-at-the-top
difficulty: 1
depends_on: []
files:
  - factory_dashboard/app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The project picker in the top bar lists the projects in the owner's order, the one on the Projects page, not by name.

### Context
Read `.softfield/cards/f193-the-project-picker-at-the-top.md` (D1).
- `factory_dashboard/app.py`: `render` builds the picker's list with its own SQL, sorted by name. Take the names from `projects_in_order` in `runner/metrics.py`, as `factory_wide_status` just above it does (the import inside the function).
- `render` still adds a project that isn't in the list (a forgotten or unknown one) at the end, and the template in `factory_dashboard/templates/base.html` doesn't change.
- The test sits beside the picker's tests in `tests/factory_dashboard/test_app.py` (`<option value=`): give the projects an order that differs from the alphabet, and assert where the options fall in the HTML.

### Done when
- the picker's options come in the projects' `priority` order, with a tie going by name, whatever the alphabet says
- after `set_project_order` in `runner/metrics.py` changes the order, the next page shows the new one
- a forgotten project is still not listed; a page opened on a project that isn't listed still shows it, last and selected
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

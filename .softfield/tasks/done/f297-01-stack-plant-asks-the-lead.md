---
id: f297-01-stack-plant-asks-the-lead
milestone: f297-the-plant-a-card-for-a
difficulty: 1
depends_on: []
files:
  - factory_dashboard/stacks_routes.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/templates/_partials/app_row.html
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
The Projects page's "Plant a card for a stack" and "Plant a card to fix it" buttons plant the card and ask the lead at once, as the Planning room's "Plant and ask the lead" does.

### Context
Read D1–D3 in `.softfield/cards/f297-the-plant-a-card-for-a.md`. `plant_value` in `factory_dashboard/stacks_routes.py` builds both buttons' request value; the runner already acts on `"ask": true` (`asks` in `runner/planner.py`), so no runner change.
- `plant_value` returns `{"text": text, "ask": true}`; fix its docstring.
- Labels: "Plant and ask the lead for a stack" (`factory_dashboard/templates/projects.html`) and "Plant and ask the lead to fix it" (`projects.html`'s Needs you line and `factory_dashboard/templates/_partials/app_row.html`).
- Their on-its-way text, in all three places: "On its way: the runner plants it and asks the lead at its next pick".
- Update the tests in `tests/factory_dashboard/test_projects.py` that name the old labels or assert `"ask": False`.

### Done when
- the stack button's and the fix button's `plant` values carry `"ask": true`
- the three buttons show the new labels, and the new on-its-way text after a press
- `test_the_projects_page_lays_out_at_phone_and_display_sizes` still passes at both sizes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1103
gate_failures: []
tokens: 593367
```

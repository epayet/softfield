---
id: f275-02-start-plate-on-top
milestone: f275-a-project-created-by-web-interface
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/projects.html
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
On the Projects page, a new project's on-its-way plate is drawn at the top of the list of projects, not at its foot, both when it comes from the page (its waiting request) and the moment "Start it" is pressed.

### Context
The picture to build: `.softfield/cards/f275-mockup/new-project-first.html` (Proposed). Read D3 in `.softfield/cards/f275-a-project-created-by-web-interface.md`, then `factory_dashboard/templates/projects.html`: the `{% for new in starting %}` loop after the projects in `#order-form .rank`, and the start script's `htmx:beforeRequest` listener, which `append`s the `#start-plate` clone to that list.
- The `proj-asked` plates are not `.proj` rows, so the order script, which reads the `.proj` rows, is not changed.
- `tests/factory_dashboard/test_projects.py` has a test asserting the waiting plate sits after the last `.proj` row (`# at the end`): it now asserts the plate comes before the first one.

### Done when
- the page draws each waiting new-project plate before the first project row of `#projects-order`
- the start script puts the plate it draws at the top of that list (`prepend`), and nothing else on the page changes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1202
gate_failures: []
tokens: 250664
```

---
id: f239-07-crashed-app-needs-you
milestone: f239-i-want-to-be-able-to-3
difficulty: 2
depends_on: [f239-05-app-row-on-projects]
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
A project whose app crashed or failed to update is a line in the Projects page's Needs you, with a link to its logs, until it runs again or is stopped.

### Context
The picture is the Needs you panel in `.softfield/cards/f239-mockup/projects-run.html` (Proposed). Read ADR 46 item 9 in `.softfield/cards/f239-i-want-to-be-able-to-3.md`, then `projects_page` and `project_cards` in `factory_dashboard/projects.py` (after f239-05, each card carries its app's `StackState`, with `word`, `detail` and `commit`) and the `projects-needs-you` section of `factory_dashboard/templates/projects.html`.
- The line: "<project>'s app crashed · <detail> · Logs" (`word` is `crashed`) or "<project>'s app didn't update to <commit> · Logs" (`update failed`), each followed by the same "Plant a card to fix it" button the row has (f239-05; reuse its partial).
- The panel shows when either the desk or an app needs the owner; its count adds both.

### Done when
- a crashed project adds its line and the panel shows even with nothing on any desk
- a running or stopped project adds none
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1624
gate_failures: []
tokens: 1671899
```

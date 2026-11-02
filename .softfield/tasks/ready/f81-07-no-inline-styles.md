---
id: f81-07-no-inline-styles
milestone: f81-assess-the-current-ui-state-of
agent: lead
difficulty: 2
depends_on: [f81-04-desk-in-classes, f81-05-thread-in-classes]
files:
  - docs/agents/developer.md
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The planning templates stay themable: a test fails when `planning.html`, `thread.html` or `proposal.html` gains a fixed inline style, and the developers' notes say where a template's look goes.

### Context
Card doc `.softfield/cards/f81-assess-the-current-ui-state-of.md` D6: before F81 these three templates held about 210 `style=` attributes, which no stylesheet change could reach; f81-04 and f81-05 moved them into `factory_dashboard/static/dashboard.css`.
- The test reads the three templates' source and allows only `style=` attributes whose every declaration is `width`, `left` or a custom property (`--…`), templated or not. Anything else names the file and line.
- `docs/agents/developer.md`: one line, in the section on the dashboard's templates (or beside the factory theme's note), that a template's look lives in `factory_dashboard/static/dashboard.css` classes on its tokens, never in `style=` but computed widths, positions and a custom property. Keep within the file's budget.

### Done when
- the test passes on main and fails when a fixed `style="color: red"` is added to any of the three templates
- `developer.md` carries the line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

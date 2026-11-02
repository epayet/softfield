---
id: bug-43-remove-the-dead-line-page
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
priority: 71
finding: f3-review
commands: [rm factory_dashboard/templates/line.html]
files:
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The dead full-page Line template is gone, and nothing says the Line is a page of its own.

### Context
Read `def _context` in `factory_dashboard/line.py` and the routes beside it, and `factory_dashboard/templates/line.html`.
- Since `/line` redirects to `/`, `factory_dashboard/templates/line.html` renders nowhere (its replay options are the old `replay`/`replayDay` values), and `_context` still says `"active": "/line"`. The partial `/line/live` renders, `factory_dashboard/templates/_partials/line.html`, stays.
- Delete the template with `rm factory_dashboard/templates/line.html` (a headless job can't delete a file otherwise), and drop `_context` if nothing else uses it.

### Done when
- `factory_dashboard/templates/line.html` is deleted, and no route or test names it
- `/line` still redirects to `/`, and `/line/live` still renders the floor
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

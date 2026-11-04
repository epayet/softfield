---
id: f81-04-desk-in-classes
milestone: f81-assess-the-current-ui-state-of
agent: developer
difficulty: 4
depends_on: [f81-03-one-button-set, f81-08-wire-square-parts]
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_coming.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
The Planning room is drawn from `dashboard.css` like the other pages: its tiles, the Plant box, Coming, the desk and Archived are panels with plate headers, their items `.desk-item` rows, with no inline styles left but a meter's width and mark.

### Context
Build the desk of the Proposed side of `.softfield/cards/f81-mockup/theme-pass.html` (`.desk-item`, `.group-head`, the desk as a `.panel`); card doc `.softfield/cards/f81-assess-the-current-ui-state-of.md` D6.
- `factory_dashboard/templates/planning.html` has about 80 `style=` attributes. Move each into a class in `factory_dashboard/static/dashboard.css`, in a block headed by a comment naming the Planning room; reuse `.panel` (plate header from f81-01), `.btn` (f81-03) and the existing `.refused`, `.desk-coming`, `.on-its-way-item`.
- A desk group's colour (`var({{ group.color }})`) stays the group's: set it as a custom property (`style="--c: var(...)"` is allowed for it) and colour `.group-head` from it.
- `blockedOnItsWay` in the page's script sets inline styles: make it add a class, so the dashed hazard edge comes from `.on-its-way-item`'s rule.
- Keep every id, `hx-*` attribute, `name`, script hook and word; the live polls select `#desk`, `#desk-coming` and `#plant-row` by id.
- Tests in `tests/factory_dashboard/test_planning.py`, `test_coming.py` and `test_thread.py` that read an inline style or the old class order read the class instead. The heading's text stays "Coming seeds": capitals come from the CSS.

### Done when
- `planning.html` has no `style=` but meter widths, the mark's position and the group's `--c`
- the Planning room shows plate headers on the tiles, Plant, Coming, the desk and Archived, in both themes, on a phone too
- a plant, a waiting plant's Save and Cancel, Try again, Set aside and Dismiss show on their way as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f279-10-overview-rows-read-right
milestone: f279-i-would-like-to-be-able
difficulty: 3
depends_on: []
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
finding: f279-i-would-like-to-be-able-F2
---

### Goal
On the Overview, Next in line's rows from the stored plan read as `/queue`'s do: a ticket's card has its " · " before it, and every row, a job too, starts with its number.

### Context
Read `factory_dashboard/templates/_partials/queue.html` (the `{% if plan %}` branch) and `factory_dashboard/queue.py` (`Row`, `Queue`, `build`).
- Today a ticket row reads "· the leadF279": the card follows the who (or the waits) with no " · ".
- Job rows have no `<span class="n">`, unlike ticket rows and every row on `/queue`.
- The `r.kind == "Planning"` branch never matches: the plan's job kind is `planner`. Remove it; a planner job is a job row like the others.
- `_build_plan_from` in `factory_dashboard/overview.py` copies each `Row` into a dict by hand. Pass `build(plan)` (a `Queue`) to the template as it is, and delete the copy.
- The two `style="…"` attributes in that branch become classes in `factory_dashboard/static/dashboard.css`, next to the other `#queue` rules.
- `test_the_queue_panel_has_the_whole_queue_link_text` in `tests/factory_dashboard/test_overview.py` matches `the lead\s*F1`, which lets the missing separator through: make it `the lead · F1`.

### Done when
- a ticket row reads "<n> <id> <goal> · the lead · F279 · <plate>", and with waits "… · the lead · <waits> · F279"
- a job row starts with its number, as on `/queue`
- a stored plan's `planner` job shows as a job row with its number
- no `style=` attribute is left in the plan branch
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

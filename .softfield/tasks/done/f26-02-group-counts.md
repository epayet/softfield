---
id: f26-02-group-counts
milestone: f26-i-want-to-see-numbers-next
difficulty: 2
depends_on: [f63-01-desk-order]
files:
  - factory_dashboard/templates/planning.html
  - tests/factory_dashboard/test_planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On `/planning`, each desk group's heading shows how many of its items still wait for the owner: "Proposals to review · 2".

### Context
Read `.softfield/cards/f26-i-want-to-see-numbers-next.md` (D2 as built, D3, D4), the `#desk` section of `factory_dashboard/templates/planning.html`, and `waiting_for_you` in `factory_dashboard/planning.py`.
- Worked example: the desk's own heading in that template, `Your desk{% if planning_count %} · {{ planning_count }}{% endif %}`, and its tests `test_desk_heading_shows_the_planning_count` and `test_desk_heading_leaves_out_what_is_on_its_way` in `tests/factory_dashboard/test_planning.py` (reuse `_groups`).
- A group's number counts its items whose `on_its_way` is false, as `waiting_for_you` does for the whole desk: an item on its way stays listed, dashed, and is not counted. Count in the template; `desk` and `DeskGroup` don't change.
- The owner (2026-10-13) reversed "totals only": `test_group_headings_get_no_number` now asserts the opposite, so replace it.
- The dashboard is English only: no translation needed.

### Done when
- every desk group shown has a heading reading its name, " · " and its number of items still waiting: with two open proposals, "Proposals to review · 2"
- the groups' numbers add up to the number in "Your desk · N" and on the Planning tab, on the same page
- after an `archive` request on a thread listed in a group, its card is still listed and that group's number is one less; a group whose items are all on their way reads its name alone, with no " · "
- the "Didn't go through" group counts its refused notes the same way
- the tests assert each heading's exact text, and would fail on main
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 183054
logs: .softfield/var/runs/20261029-043403/f26-02-group-counts
```

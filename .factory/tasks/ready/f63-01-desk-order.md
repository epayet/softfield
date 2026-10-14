---
id: f63-01-desk-order
milestone: f63-i-want-to-see-cards-in
difficulty: 2
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
`/planning` shows what matters most first: Coming, then Plant an idea, then the desk with sign-offs before proposals before conversations before seeds, then Archived.

### Context
Read `.factory/cards/f63-i-want-to-see-cards-in.md` (Outcome, D1–D5), `factory_dashboard/templates/planning.html` and `desk` in `factory_dashboard/planning.py`.
- `desk()` returns the groups in a new order: `refused`, `ripe`, `proposals`, `answers`, `seeds`. Keys, colours and items are unchanged; only the `ripe` group's name changes, to "To sign off". Update its docstring and the module docstring.
- `waiting_for_you` and `desk_trail` (F35), the Overview's Needs you and the tab count read `desk()`: they follow without change.
- In the template, `#desk-coming` moves out of the flex row to just above it, full width, still only `{% if coming.items %}`; the row keeps `#plant` then `#desk`.
- Tests that index the groups by position (`desk(...)[3]`, `desk(...)[4]`, `test_desk_returns_the_five_groups_in_order_empty_ones_too`) change to the new order.
- **Change only the order and the one name: no item's words, link or condition changes.**

### Done when
- `desk()` names its groups, in order: "Didn't go through", "To sign off", "Proposals to review", "Your answers wanted", "Seeds, not asked about yet"
- on `/planning` with a plant on its way, `id="desk-coming"` comes before `id="plant"`, which comes before `id="desk"`; with nothing on its way there is no `desk-coming`
- with a ripe card, an open proposal and an answered thread, the desk lists the ripe card first, then the proposal, then the thread, and `desk_trail`'s Next from the planning page is the ripe card's page
- `id="archived"` is still last
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

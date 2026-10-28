---
id: f63-02-blocked-stays-second
milestone: f63-i-want-to-see-cards-in
agent: developer
difficulty: 2
finding: f63-i-want-to-see-cards-in-F2
depends_on: [f63-01-desk-order]
files:
  - factory_dashboard/planning.py
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_proposal.py
  - tests/factory_dashboard/test_thread.py
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_proposal.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
On the desk, "Blocked tickets" is second again, right after "Didn't go through", as F106 D1 decided; the rest keeps F63's order.

### Context
f63-01 reordered `desk()` in `factory_dashboard/planning.py` and moved the `blocked` group to last, which its ticket never asked for. F106 D1 (`.factory/cards/f106-where-do-blocked-tickets-go-for.md`) put it second: a blocked ticket stops the tickets behind it, and like "Didn't go through" it is usually empty.
- `desk()` returns, in order: `refused`, `blocked`, `ripe`, `proposals`, `answers`, `seeds`. Keys, names, colours and items are unchanged. Update its docstring to say so.
- Tests that pick a group by its position (`desk(db, PROJECT, NOW)[1]`, `[2]`, `[3]`, `[4]`, `[5]` in the three test files) pick it by its key instead, through one helper in `tests/factory_dashboard/test_planning.py`, `_group(db, key)`, returning that group's items. The `blocked` tests already do it inline with `next(g for g in desk(...) if g.key == "blocked")`; use the helper there too.
- `test_desk_returns_the_five_groups_in_order_empty_ones_too` becomes `test_desk_returns_the_six_groups_in_order_empty_ones_too`, with "Blocked tickets" second in its two lists.
- `test_two_blocked_tickets_appear_second_on_the_desk_with_their_ids_and_reason` also asserts that `desk()`'s second group's key is `blocked`.
- **Change only the order: no item's words, link or condition changes.**

### Done when
- `desk()` names its groups, in order: "Didn't go through", "Blocked tickets", "To sign off", "Proposals to review", "Your answers wanted", "Seeds, not asked about yet"
- no test reads a desk group by its index, except the order tests
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

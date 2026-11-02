---
id: f185-01-answers-before-proposals
milestone: f185-i-changed-my-mind-i-want
difficulty: 2
depends_on: []
files:
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_coming.py
---

### Goal
On the owner's desk, "Your answers wanted" comes right after "To sign off" and before "Proposals to review", and its answered threads come newest reply first.

### Context
Read `.softfield/cards/f185-i-changed-my-mind-i-want.md` (Outcome, D1–D3), and `desk` and `_answers_wanted` in `factory_dashboard/planning.py`. `.softfield/tasks/done/f63-01-desk-order.md` made the last change to this order and is the example to follow.
- `desk()` returns its groups in this order: `refused`, `blocked`, `ripe`, `answers`, `proposals`, `seeds`. Keys, names, colours and items are unchanged. Update its docstring.
- In `_answers_wanted`, the settled `items` (the lead's reply is the thread's latest) come newest message first. The on-its-way items after them (`placed + rest + later`, F84 D4) keep their order. `_last_messages` stays oldest first, since other callers rely on it.
- `waiting_for_you`, `desk_trail` (F35), the Overview's Needs you, the Planning tab's count and the Projects page read `desk()`, so they follow without change.
- Tests that list the groups in order (`["ripe", "proposals", "answers", "seeds"]` in both test files, `test_desk_returns_the_six_groups_in_order_empty_ones_too`) change to the new order.
- **Change only these two orders: no item's words, link or condition changes.**

### Done when
- `desk()` names its groups in order: "Didn't go through", "Blocked tickets", "To sign off", "Your answers wanted", "Proposals to review", "Seeds, not asked about yet"
- with a ripe card, an answered thread and an open proposal, `/planning` lists the ripe card first, then the thread, then the proposal, and `desk_trail`'s Next from the ripe card's page is the thread's page
- with two threads the lead answered, the one with the later reply is listed first in Your answers wanted; a thread the lead still owes a reply is listed after both
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 158873
logs: .softfield/var/runs/20261029-222125/f185-01-answers-before-proposals
```

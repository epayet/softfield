---
id: f51-01-desk-counts-what-waits-on-you
agent: lead
milestone: f51-when-a-plan-depends-on-an
difficulty: 3
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
The owner's desk lists only what they can do now: a card's plan waiting on its ADR is folded into the ADR's item, and a thread the owner has answered leaves "Your answers wanted".

### Context
Read `_answers_wanted`, `_open_proposals`, `_about`, `_settled` and `_adr_waits` in `factory_dashboard/planning.py`; the tests for Coming and the desk in `tests/factory_dashboard/test_planning.py` are the example to follow. The Planning tab's count and the Overview's Needs you both count `desk(...)` items, so fixing the desk fixes them.
- The owner (2026-10-08): "i can't do anything about it, so it shouldn't count as something on my desk".
- D1 (`.factory/cards/f51-when-a-plan-depends-on-an.md`): while a card's latest proposals hold an open `adr` proposal (not settled by `_settled`) whose ADR `_adr_waits` reports as waiting, that card's `plan` and `replan` proposals are not desk items; the ADR's item's words end with " · then its plan". Mock-ups, merges and seeds are unchanged.
- D4: `_answers_wanted` skips a thread with an open `plan_message` request (`kind = 'plan_message'`, `done IS NULL`, `subject` = the card). `coming()` already lists it.
- `_open_proposals` needs the repo for `_adr_waits`: pass `_repo(conn, project)` down from `desk`; with no repo (a URL), keep today's behaviour.

### Done when
- a card with an open ADR proposal (its file Proposed on main) and a plan proposal: the desk has one item for that card, the ADR's, its words ending "then its plan", and the Planning tab's count is 1, not 2
- once an `accept_adr` request for that ADR exists, the ADR's item is gone and the plan's item is back
- a card whose ADR is Accepted on main shows its plan as today
- a thread whose last message is the lead's, with an open `plan_message` request: not in "Your answers wanted", in Coming; the count drops by one
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

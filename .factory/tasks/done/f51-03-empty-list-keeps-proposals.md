---
id: f51-03-empty-list-keeps-proposals
milestone: f51-when-a-plan-depends-on-an
difficulty: 2
depends_on: []
files:
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A lead reply that lists no proposals leaves the thread's earlier proposals open, with their buttons, on the thread and on each proposal's page, as the desk already does.

### Context
Read `_proposals`, `_standing` and `proposal_review` in `factory_dashboard/planning.py`, and `test_a_proposal_from_an_older_reply_is_replaced` in `tests/factory_dashboard/test_planning.py` as the example to follow.
- What happened (2026-10-20, F51's thread): a lead reply with no proposals is stored as the text `'[]'`, not NULL. `_proposals` and `proposal_review` pick "the latest lead message with proposals" with `r["proposals"]`, which is true for `'[]'`. So that reply hid the earlier list, and each proposal's page said "replaced by a newer reply"; the owner couldn't approve the replan.
- `_open_proposals` (the desk) already skips `'[]'` in its SQL: the thread and the review page must read the same way. Keep one helper for "a lead message that lists proposals" and use it in both places.

### Done when
- a lead message with a replan, then a lead message whose proposals are `'[]'`: the thread lists the replan with its buttons, and its review page shows it open, not "replaced by a newer reply"
- a later lead message with a different proposal still replaces the earlier ones, as `test_a_proposal_from_an_older_reply_is_replaced` checks
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1899
gate_failures: []
tokens: 1752692
```

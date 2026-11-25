---
id: f293-01-no-points-they-know
milestone: f293-a-lot-of-conversation-points-are
difficulty: 2
agent: lead
files:
  - runner/prompts.py
  - runner/instructions/author/owner.md
  - tests/runner/test_prompts.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
The planner stops telling the owner what they already know: no points about the order of the dashboard's buttons (accept the ADR before the plan, a ticket relies on ADR N, the plan waits for Approve), and no "No mock-up" point on work with nothing on screen.

### Context
Read `.softfield/cards/f293-a-lot-of-conversation-points-are.md` (What we found, D1–D3). Write the tests first.
- `_PLANNER_HEAD` in `runner/prompts.py`, the "How to answer" list: add D1's bullet next to "No point reports that a check found nothing". Give the examples it names, and say why: the dashboard says these itself and refuses an approval out of order with its reason. Say a real choice an ADR carries still gets a point.
- The mock-up bullet in `PLANNER` (the one starting "- A card that changes what a page shows"): add D2's few words. Keep "say why in a point", since `test_a_card_that_changes_a_page_gets_a_today_proposed_mockup_unasked` checks it.
- `runner/instructions/author/owner.md`, under "Reporting": one dated bullet for D3 (2026-11-24, F293), a rule, not a story.
- `PLANNER_GENERAL` shares `_PLANNER_HEAD`, so D1 reaches the general thread too. That is intended.

### Done when
- `PLANNER` and `PLANNER_GENERAL` both ask for no point about accepting an ADR before its plan, a ticket relying on an ADR, or a plan waiting for Approve, and say the dashboard tells the owner itself
- `PLANNER`'s mock-up bullet says work with nothing on screen gets no point about a mock-up
- `owner.md` carries the preference once, dated 2026-11-24
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

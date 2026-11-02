---
id: f37-01-names-beside-numbers
milestone: f37-in-planning-mode-it-tends-to
agent: lead
difficulty: 2
depends_on: []
files:
  - docs/agents/owner.md
  - runner/prompts.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
Every lead job writes a few words beside each card, ticket, ADR or decision number the owner reads.

### Context
Read `.softfield/cards/f37-in-planning-mode-it-tends-to.md` D1, the "Name a card with its title" line in `_PLANNER_HEAD` (`runner/prompts.py`) and the test that checks it in `tests/runner/test_prompts.py`.
- `docs/agents/owner.md` gains one dated rule beside "The dashboard (owner, 2026-10-02)", in its style: a card with its title ("F22, Archive at the bottom"), a ticket, an ADR or a decision with a few words saying what it is ("ADR 29, the lead looks at a blocked ticket"), a decision ("D2") said in words and never alone. Owner, 2026-10-26: "I prefer small summaries next to the number whenever mentioned, and with links when relevant."
- The planner's line grows to the same rule; keep the words "F22, Archive at the bottom" and "never a bare number" that the test checks.

### Done when
- `docs/agents/owner.md` holds the rule once, dated 2026-10-26
- the planner's prompt says a ticket, an ADR and a decision get a few words beside them too
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

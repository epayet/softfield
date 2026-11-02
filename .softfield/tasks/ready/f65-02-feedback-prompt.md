---
id: f65-02-feedback-prompt
milestone: f65-what-happens-if-i-comment-on
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/planner.py
  - runner/prompts.py
  - runner/loop.py
tests:
  - tests/runner/test_planner.py
---

### Goal
A message on a card that waits for sign-off reaches the lead as feedback on built work, with the card's current What changed.

### Context
Read `.softfield/cards/f65-what-happens-if-i-comment-on.md` (D4), then `prompt` in `runner/planner.py`, `PLANNER` in `runner/prompts.py`, the planner job's call in `runner/loop.py` (`planner.prompt(thread, text, comments, threads, earlier)`), and `signoff_sections` in `runner/milestone.py`.
- Ripe here means what `_field` in `factory_dashboard/line.py` means: every ticket done and the sheet stored.
- The added lines say: the card is built and waits for the owner's sign-off; answer a question on the thread; draft follow-up tickets in .softfield/tasks/later/ only for a change; small, unprotected ones follow an example and go to a developer.

### Done when
- on a ripe card, the prompt says it waits for sign-off and quotes its What changed (or This round, when there is one)
- on any other card, and on the general thread, the prompt is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

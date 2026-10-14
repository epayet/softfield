---
id: f25-01-still-needed
milestone: f25-whenever-i-plant-something-does-it
difficulty: 2
depends_on: []
agent: lead
files:
  - runner/prompts.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
Before the lead answers a message in the planning room, it checks whether the seed is still needed: done already, made moot by later work, or open.

### Context
Read `_PLANNER_HEAD` in `runner/prompts.py` (its "Before answering, look for a repeat (f6-12)" paragraph) and `test_both_planner_prompts_look_for_duplicates_and_propose_a_merge` in `tests/runner/test_prompts.py`, the example to extend. F25's Decisions D1–D3 in `.factory/cards/f25-whenever-i-plant-something-does-it.md`.
- The owner (2026-10-07): "whenever i plant something, does it check the current state of things in case the seed is not relevant anymore?"
- Keep it to two or three sentences in the same paragraph, in the prompt's plain style.

### Done when
- Both `PLANNER` and `PLANNER_GENERAL` ask, before answering, whether the seed is still needed, reading the code it is about and `git log`, not only the plan.
- The repeat check covers the cards in .factory/cards/ in every state (building and done too), not only idea, planning and ready.
- A seed already done is said as the first point, naming the commit or card, with the suggestion to drop it; one a building card covers is a `merge` into that card.
- The listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

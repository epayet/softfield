---
id: f303-03-how-to-fix
milestone: f303-from-a-factory-suggestion-add-a
difficulty: 2
depends_on: [f303-03-how-to-split]
files:
  - runner/instructions/lead.md
  - runner/prompts.py
tests:
  - tests/runner/test_prompts.py
agent: lead
area: factory
---

## Goal
Tell the lead never to work around a `size` or `imports` failure, and to answer a ticket blocked by one with a planned move (ADR 55 item 6).

## Context
- `.softfield/adr/55-a-file-at-its-size-limit-is-split-by-plan.md` item 6: the rule, in plain words.
- `runner/instructions/lead.md` "Tickets": one bullet: a headless lead job never splits, trims or moves code to get past `size` or `imports`; it leaves the check failing and the runner blocks the ticket. "Planning room", the bullet on a replan bringing back blocked tickets: one line that a `size` or `imports` block is answered with a move-only lead ticket first, the blocked ticket after it.
- `runner/prompts.py`: `PLANNER`'s rules for the look at a blocked ticket get the same line.
- `tests/runner/test_prompts.py` checks the prompts' content: add a test that `PLANNER` answers a `size` or `imports` block with a move-only ticket first.

## Done when
- `runner/instructions/lead.md` and `prompts.PLANNER` say item 6, each in its own place, briefly
- the listed `tests:` pass, and fail without the change
- all gates pass

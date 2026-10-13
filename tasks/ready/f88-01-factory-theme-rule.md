---
id: f88-01-factory-theme-rule
milestone: f88-add-to-lead-memory-that-new
depends_on: [f72-01-mockup-by-default]
agent: lead
difficulty: 2
priority: 1
area: factory
files:
  - docs/agents/owner.md
  - docs/agents/lead.md
  - runner/prompts.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
New factory features and their mock-ups are designed in the factory theme from the first draft, leaning bolder, inspired by Arknights: Endfield's industrial look without copying anything from it.

### Context
Read F88's Decisions D1–D5 in `docs/milestones/f88-add-to-lead-memory-that-new.md`, the tokens and fonts at the top of `factory_dashboard/static/dashboard.css`, the mock-up paragraph f72-01 added to `PLANNER` in `runner/prompts.py`, and its test in `tests/runner/test_prompts.py`.
- The owner (2026-10-09): "new software factory features should be done with the main theme. the inspiration source is arknight endfield factory system … it should be subtle though and not copyright issue … i can tone down if necessary in proposals/mock ups, rather than tone up to be more fun".
- `owner.md` holds rules, not stories (F21 D3): keep the new preference to a few lines.

### Done when
- `docs/agents/owner.md` has a "Factory theme" preference dated 2026-10-09: the traits of D1 (pointing at `dashboard.css`'s tokens), the guard of D2 (Endfield named as the mood only; nothing taken from it; the word never on a page or asset), D3 (ornament never uses a status colour), D4 (proposals lean bolder, the owner tones down) and D5 (the factory only).
- `docs/agents/lead.md`'s Planning room has one line pointing at it.
- `PLANNER`'s mock-up paragraph says a mock-up's Proposed is drawn in the factory theme from `dashboard.css`'s tokens, leaning bolder, with nothing copied from a game. It doesn't name the game.
- A test in `tests/runner/test_prompts.py` checks that `PLANNER` asks for the factory theme in mock-ups and that neither `PLANNER` nor `PLANNER_GENERAL` contains "Endfield".
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

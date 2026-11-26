---
id: f303-03-how-to-split
milestone: f303-from-a-factory-suggestion-add-a
difficulty: 2
depends_on: [f303-04-imports-at-top]
files:
  - AGENTS.md
  - runner/instructions/lead.md
  - runner/prompts.py
tests:
  - tests/runner/test_prompts.py
agent: lead
area: factory
---

## Goal
Write down how a file that is too big is split and how an import cycle is fixed, and tell the planner to plan that ahead, so it is done along the architecture, never as a workaround (ADR 55 items 7 and 8).

## Context
- `.softfield/adr/55-a-file-at-its-size-limit-is-split-by-plan.md` items 7 and 8: the rules, in plain words.
- `AGENTS.md` item 5 names the code's edges; add item 7's two rules there in two or three sentences: a file is split by what it does, along those edges, the new module named for its job with its own test file (item 9) and no behaviour change; never a `_helpers`, `_utils`, `_2` or `_part` module, never comments deleted to fit; a cycle is fixed by moving the shared code down to a module both can import, never by copying it or importing inside a function. Name no runner, gate or ticket there (ADR 41).
- `runner/instructions/lead.md` "Plan": one bullet for item 8 (a plan whose tickets grow a file within 10% of its `[checks]` limit, or need code from a module that imports theirs, puts a move-only lead ticket first, as F290 did).
- `runner/prompts.py`: `PLANNER`'s rules get item 8 in one line.
- `tests/runner/test_prompts.py` checks the prompts' content: add a test that `PLANNER` asks for the split or move first.
- Answering a block is `f303-03-how-to-fix`'s, not this one's.

## Done when
- `AGENTS.md` item 5 says both rules, briefly, with no factory machinery named
- `runner/instructions/lead.md` and `prompts.PLANNER` say item 8, briefly
- the listed `tests:` pass, and fail without the change
- all gates pass

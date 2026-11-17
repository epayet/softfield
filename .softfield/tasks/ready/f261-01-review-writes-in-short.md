---
id: f261-01-review-writes-in-short
milestone: f261-the-review-notes-on-the-planning
difficulty: 2
depends_on: [f216-01-review-sheet-new-shape]
agent: lead
files:
  - runner/prompts.py
  - runner/instructions/lead.md
  - runner/milestone.py
tests:
  - tests/runner/test_prompts.py
  - tests/runner/test_milestone.py
---

### Goal
A milestone review opens its sign-off sheet with "In short": two lines the planning room shows above everything else.

### Context
Read `.softfield/cards/f261-the-review-notes-on-the-planning.md` (D1). f216-01 has already reshaped the sheet to nine numbered headings; this adds one before them.
- `REVIEW` in `runner/prompts.py`: the sheet's headings start with `### In short`: at most two lines, what the card does now and whether it matches its plan and mock-up. Not a list, no heading of its own inside.
- `runner/instructions/lead.md`, "Sign-off sheet": the same, in one line.
- `SIGNOFF_SECTIONS` in `runner/milestone.py` gains `"In short": "in_short"`.

### Done when
- `REVIEW` asks for `### In short` first, at most two lines, and says it is never left out
- `signoff_sections` on a sheet with `### In short` returns `in_short`, and a sheet without it parses as before
- `runner/instructions/lead.md` says the same as `REVIEW`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

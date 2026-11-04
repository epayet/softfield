---
id: f216-01-review-sheet-new-shape
milestone: f216-let-s-redesign-the-milestone-review
difficulty: 3
depends_on: [f164-01-reviews-quote-their-ideas]
agent: lead
files:
  - runner/prompts.py
  - runner/instructions/lead.md
  - runner/milestone.py
  - docs/workflow.md
tests:
  - tests/runner/test_prompts.py
  - tests/runner/test_milestone.py
---

### Goal
A milestone review writes the new sign-off sheet, with "Decisions made along the way" and "Done when, as of now", and writes nothing below the sheet but the runner's numbers.

### Context
Read `.softfield/cards/f216-let-s-redesign-the-milestone-review.md` (D1, D2, D3, D5, D6, D7).
- `REVIEW` in `runner/prompts.py`: the lines from "Also create or update" name the sheet and what follows it. Replace them with D1 and D6, and keep the report block's markers. It keeps F164's rule for quoted ideas under What next.
- `runner/instructions/lead.md`, "Sign-off sheet": the list becomes D1's nine headings, with D2's, D3's and D5's rules in a line or two each.
- `SIGNOFF_SECTIONS` in `runner/milestone.py` gains D7's two keys. `signoff_sections` needs no other change: its heading form takes any number.
- `docs/workflow.md`, the "Report" paragraph, says what D6 says.

### Done when
- `REVIEW` asks for the nine headings in D1's order, says a section with nothing to say is left out except What changed and How to test, and no longer asks for what was built, findings and resolutions, what was set aside or workflow observations
- `REVIEW` says what belongs under "Decisions made along the way" and what doesn't, as D2 says, and that its source is the card's Decisions, Done when and mock-up against the diff and the review's own fixes
- `signoff_sections` on a sheet with the new headings returns `done_check` and `along_the_way`, and a sheet without them still parses as before
- `runner/instructions/lead.md` and `docs/workflow.md` say the same as `REVIEW`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

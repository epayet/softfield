---
id: f164-01-reviews-quote-their-ideas
milestone: f164-i-like-reading-the-milestone-reviews
difficulty: 2
depends_on: []
agent: lead
files:
  - runner/prompts.py
  - docs/agents/lead.md
tests:
  - tests/runner/test_prompts.py
---

### Goal
A milestone review writes every suggestion that needs a card as one quoted `> ` line under its Product or Factory bullet in "6. What next", so the dashboard can offer to plant it.

### Context
Read `.factory/cards/f164-i-like-reading-the-milestone-reviews.md` (D1).
- `REVIEW` in `runner/prompts.py`: the sentence on "6. What next" gets D1's rule, in a line or two.
- `docs/agents/lead.md`, "Sign-off sheet", item 6: the same rule, worded for the lead.
- The shape to ask for is the one F19's review already uses: `.factory/reviews/f19-will-i-need-to-refresh-planning.md`, "6. What next".

### Done when
- `REVIEW` asks for each suggestion that needs a card as one `> ` line under its Product or Factory bullet, one self-contained sentence in the owner's plant-note voice, and says what the review already did itself is not quoted
- `docs/agents/lead.md` item 6 says the same
- a test in `tests/runner/test_prompts.py` checks `REVIEW` asks for the quoted line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

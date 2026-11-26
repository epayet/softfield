---
id: f301-02-owner-rule-what-changed-first
milestone: f301-the-what-it-s-about-section
difficulty: 1
depends_on: []
agent: lead
files:
  - runner/instructions/author/owner.md
tests:
  - tests/runner/test_prompts.py
---

### Goal
The owner's rule on what a milestone view shows first matches what they asked on F301: on a reviewed card, what changed comes first.

### Context
Read `.softfield/cards/f301-the-what-it-s-about-section.md` (D5). In `runner/instructions/author/owner.md`, the bullet "Expected against actual, first" says the expected outcome and Done when come first on any milestone view or report.

### Done when
- the bullet says: on a reviewed milestone, what changed comes first, with any Done when line not yet met at its head; the expected outcome and the rest of Done when fold behind it; before the review, the expected outcome and Done when stay first; dated (owner, 2026-11-25, F301)
- nothing else in the file changes
- a test in `tests/runner/test_prompts.py` checks the lead's system prompt (which carries owner.md) says a reviewed milestone shows what changed first
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

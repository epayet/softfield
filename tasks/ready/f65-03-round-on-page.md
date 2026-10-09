---
id: f65-03-round-on-page
milestone: f65-what-happens-if-i-comment-on
difficulty: 4
depends_on: [f65-01-review-rounds]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A card's page opens its review on the latest round: "Round N: what changed since your comment", the comment quoted, then the earlier sheet under "Earlier".

### Context
Read `docs/milestones/f65-what-happens-if-i-comment-on.md` (D3) and the picture `docs/milestones/f65-mockup/round.html`, then `_SHEET`, `class Review` and `_review` in `factory_dashboard/planning.py`, and the `#review` section of `factory_dashboard/templates/thread.html`. Then the F50 tests of the review section in `tests/factory_dashboard/test_planning.py`, the example to follow.
- Once a round's review is written (f65-01), the stored sheet (`milestones.signoff`, JSON) also has `round` (the lead's Markdown), `round_no` (N) and `asked` (the owner's comment, plain text). Without `round`, the page is as today.

### Done when
- with a `round` in the sheet, the review section starts with "Round N: what changed since your comment", the owner's comment quoted, then the round's text
- the first sheet's What changed, How to test and Decisions show below, under "Earlier"
- without a `round`, the section is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f85-07-review-lists-changed-pages
milestone: f85-when-i-sign-off-a-task
agent: lead
difficulty: 3
depends_on: [f85-06-fix-unstyled-page-not-a-picture]
files:
  - runner/prompts.py
  - runner/milestone.py
tests:
  - tests/runner/test_prompts.py
  - tests/runner/test_milestone.py
---

### Goal
A card whose work changed what a page shows gets before and after pictures even when its plan listed no pages: the review lists them in round 1, and the runner takes the pictures right after that round.

### Context
Read D1, D2 and D13 and "Unstyled and missing pictures" in `.softfield/cards/f85-when-i-sign-off-a-task.md`. Then `REVIEW` in `runner/prompts.py` (the paragraph on the card's after pictures), and in `runner/milestone.py` `review_milestone` (where `shots.take` runs before each round) and `review_pictures`. `pages` in `runner/shots.py` reads the list.
- `REVIEW`: in round 1, when the diff changes what a page shows (a template, a stylesheet, a page's script or view) and the card doc has no `## Before and after`, add that section to the card doc, one backticked address per changed page, as the planner's brief words it (`PLANNER`, the mock-up paragraph). In a project without `[shots]` it still writes the list. It doesn't compare pictures it hasn't seen: "What changed" says the pictures were taken after the review.
- `review_milestone`: after a round's job, when `pages` of the card doc differs from what it was before the job, call `shots.take` again, so the pictures, before included, are on the card's page before the owner reads it. Nothing else changes when the list didn't move.
- A card that already lists its pages is untouched.

### Done when
- `REVIEW` formatted for round 1 asks for the section when the card doc has none, and round 2's doesn't
- a review round whose job adds `## Before and after` to the card doc is followed by pictures of those pages, before and after; a round that leaves the list as it was takes none after its job
- the listed `tests:` pass, and fail without the change
- all gates pass (see `runner/instructions/workflow.md`)

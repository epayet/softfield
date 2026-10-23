---
id: f164-03-idea-plates-with-plant
milestone: f164-i-like-reading-the-milestone-reviews
difficulty: 4
depends_on: [f164-02-review-ideas-and-their-state, f164-02b-fix-review-ideas-lookup]
agent: lead
files:
  - factory_dashboard/planning.py
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/_partials/idea.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
Each idea of a review shows as a plate with Plant and Plant and ask the lead, on the card's thread and in place on its milestone page; a press shows it on its way at once, and a planted one links to its card.

### Context
Read `.factory/cards/f164-i-like-reading-the-milestone-reviews.md` (D4, D5) and build the mock-up's Proposed, `.factory/cards/f164-mockup/review-ideas.html`.
- The ideas come from `review_ideas` in `factory_dashboard/milestones.py` (f164-02).
- Thread: `_review` in `factory_dashboard/planning.py` and the `#review` section of `factory_dashboard/templates/thread.html`: "Ideas from this review · N" after the sections, before "The whole review".
- Milestone page: `_to_html` in `factory_dashboard/milestones.py` renders the sheet; each quoted line is drawn in place by the new partial `factory_dashboard/templates/_partials/idea.html`, which both pages use.
- The buttons post as the Plant box in `factory_dashboard/templates/planning.html` does, value `{text, ask, area, from}` (D4), to the idea's project; the on-its-way swap follows Sign off's `hx-on::before-request` in `factory_dashboard/templates/thread.html`.
- Styles in `factory_dashboard/static/dashboard.css` from the existing tokens only (`--factory`, `--product`, `--hazard`, `--rule`, `--plate`).

### Done when
- F19's thread, with its sheet and F166's plant stored, shows "Ideas from this review · 1" and a plate linking to `/planning/f166`, with no buttons
- an idea with no plant shows both buttons; Plant posts a `plant` request whose value carries the idea's text ending "From F28's review.", `ask` false, its area and its id as `from`; Plant and ask the lead posts `ask` true
- an idea on its way shows "On its way · planted at the runner's next pick" in a dashed hazard plate and no buttons, on both pages, after a reload too; a refused one shows "Didn't go through:" and its words, with the buttons back
- the milestone page shows each quoted line as a plate where it stood, and no "&gt;" text
- a factory idea of another project's review posts to the factory's own project and its plate says "for Softfield" (the project's name)
- a sheet with no quoted line shows no ideas heading
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

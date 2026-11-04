---
id: f216-03-review-page-plates-and-folds
milestone: f216-let-s-redesign-the-milestone-review
difficulty: 5
depends_on: [f216-01-review-sheet-new-shape, f216-02-findings-costs-and-markdown, f164-03-idea-plates-with-plant]
agent: lead
files:
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/milestones.py
  - factory_dashboard/thread.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
A card's page, once its review is written, reads as the mock-up's Proposed: one kind of plate, the reading part first, Sign off after it, and everything else in closed folds that say what's inside.

### Context
Read `.softfield/cards/f216-let-s-redesign-the-milestone-review.md` (D3, D4, D8, D9, D10, D11, D13) and build Proposed in `.softfield/cards/f216-mockup/review-page.html`. Its dashed outlines and green notes belong to the mock-up, not the page.
- `factory_dashboard/templates/milestone.html`: the `{% if milestone.signoff %}` branch gets the new order; a card with no sheet keeps today's page. Keep the ids `what-changed`, `how-to-test`, `decisions`, `what-next`, `later`, `lessons`, `clogged`, `results`, `tickets`, `runs`, `shots` on their new parts, so the tests and any link still find them. `findings` and `savings` move into What it cost.
- `milestone_detail` in `factory_dashboard/milestones.py`: pass `done_check` and `along_the_way` through `signoff_html`, drop a `decisions` that starts "none", and work out D9's gists. `caught` and `spend` are f216-02's.
- `_SHEET` and `_review` in `factory_dashboard/thread.py`, per D13.
- `factory_dashboard/static/dashboard.css`: `.about` and `.shots` have the same plate rules. Share them under one selector and draw the new parts with it, from the existing tokens only. The `#review` block's inline styles and the sections' bare `h2`s go.
- F164's idea plates stay in place inside What next.

### Done when
- with a stored sheet, the page's parts come in D8's order, and Sign off comes after Decisions made along the way and before What next
- the eight folds are closed `<details>` in one "Behind it" plate, each with its gist, and a part with nothing in it isn't drawn: no "Not written yet", "No runs." or "No savings data."
- a sheet with `done_check` shows it in place of the plan's Done when; a sheet without it shows the plan's list
- a `decisions` starting "None" (F187's) shows no plate on the page or the thread; F175's shows "Needs your answer" straight under the head
- What the review caught and What it cost draw `caught` and `spend`, with no separate Findings, Results or Savings parts; savings show only when `savings.lines` is above 0
- a card with no sheet draws as before
- the thread's review shows Decisions made along the way when the sheet has it
- no horizontal scroll at 390 px on F187's page, and tapping a fold works without a script
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

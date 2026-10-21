---
id: f165-01-point-opens-its-proposal
milestone: f165-there-s-been-a-few-conversations
difficulty: 2
depends_on: []
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A mock-up proposal's review page always shows its picture: one listed under its old path (`docs/milestones/…-mockup/`) is read where the file lives now, and one whose file is gone says so instead of showing nothing.

(The file name is from the card's first draft, which put a link on each point; the owner turned that down and a planner job can't rename a file. The goal above is the ticket.)

### Context
Read `.factory/cards/f165-there-s-been-a-few-conversations.md` (D1) and the mock-up to build, `.factory/cards/f165-mockup/point-links.html` (Proposed).
- In `factory_dashboard/planning.py`: `proposal_review` (its `mockup` value), `_MOCKUP_RE` and `mockup_file`. The mock-up is read with `draft` from `runner/planner.py` (the plan branch while it exists, else main).
- ADR 30's move (commit f13bc3c) put every `docs/milestones/<name>-mockup/<file>` at `.factory/cards/<name>-mockup/<file>`. Proposals stored before it still name the old path: F8, F17, F54, F65, F67 and F68, F94 on softfield's threads.
- A stored path `docs/milestones/<name>-mockup/<file>` becomes `.factory/cards/<name>-mockup/<file>` for the frame. Don't change the stored proposals.
- When the mock-up's file can't be read (`draft` returns None) the page shows, where the frame would be, "The mock-up's file isn't in the repo any more, so there is nothing to show." and the stored path, as the mock-up draws it, with the existing tokens only.
- The tests to follow: `test_the_mockup_route_serves_the_plan_branchs_mockup_and_nothing_else` and `test_a_mockups_scripts_run_in_the_review_pages_frame_as_no_one` in `tests/factory_dashboard/test_planning.py`.
- Change nothing in `runner/`.

### Done when
- a `mockup` proposal whose path is `docs/milestones/f67-mockup/review.html`, with `.factory/cards/f67-mockup/review.html` on main, shows a frame whose address ends in `.factory/cards/f67-mockup/review.html`, and the mock-up route serves it
- a `mockup` proposal whose file is on neither path shows the "isn't in the repo any more" line and no frame
- a proposal already under `.factory/cards/` shows as today; a `plan` shows no frame and no line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

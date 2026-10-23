---
id: f165-03-fix-old-path-mockup-has-no-test
milestone: f165-there-s-been-a-few-conversations
difficulty: 2
depends_on: []
files:
  - tests/factory_dashboard/test_planning.py
tests:
  - tests/factory_dashboard/test_planning.py
finding: f165-01-point-opens-its-proposal-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f165-01-point-opens-its-proposal's tests: nothing tests that a mock-up listed under its old path shows its frame.

### Context
By the lead at a checkpoint, on the merge of `.factory/tasks/done/f165-01-point-opens-its-proposal.md`. The code looks right; its tests cover only the "file gone" case (`test_a_mockup_gone_shows_its_message_and_no_frame`). The ticket's first Done-when line has no test: a `mockup` proposal whose stored path is `docs/milestones/<name>-mockup/<file>` while the file is at `.factory/cards/<name>-mockup/<file>`.
- Follow `test_the_mockup_route_serves_the_plan_branchs_mockup_and_nothing_else` and `test_a_mockups_scripts_run_in_the_review_pages_frame_as_no_one` in `tests/factory_dashboard/test_planning.py` for the fixtures (`planning`, `serve`, `checkout`, `_review`, `_review_page`).
- Change only tests; they pass on main's code.

### Finding
f165-01-point-opens-its-proposal-1, should-fix: in `tests/factory_dashboard/test_planning.py`, no test for the old-path-resolved case; deleting `_resolve_mockup_path`'s old-path branch in `factory_dashboard/planning.py` leaves every test green.

### Done when
- a test stores a `mockup` proposal with path `docs/milestones/f67-mockup/review.html`, with the file at `.factory/cards/f67-mockup/review.html` on the plan branch or main; the review page's `#mockup` frame has a `src` ending in `.factory/cards/f67-mockup/review.html`, there is no "gone" block, and a request to that `src` returns the file's content
- a `plan` proposal shows no frame and no "gone" block
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

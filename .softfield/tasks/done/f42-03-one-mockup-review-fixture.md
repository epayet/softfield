---
id: f42-03-one-mockup-review-fixture
milestone: f42-the-space-for-me-to-scroll
agent: developer
difficulty: 2
tests_only: true
finding: f42-the-space-for-me-to-scroll-F2
depends_on: [f42-02-top-bar-steps-aside]
files:
  - tests/factory_dashboard/test_proposal.py
  - tests/factory_dashboard/test_thread.py
tests:
  - tests/factory_dashboard/test_proposal.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
The mock-up review's test setup is written once, in one helper, instead of copied into five tests.

### Context
f42-01 copied the same twelve lines (make `plan/f6` with the f6-mockup folder's index.html and the Proposed ADR, commit, back to `main`, then `_review(conn, planning, "f6", _REVIEW_MOCKUP)`) into `test_a_mockup_link_is_visible_on_a_phone` and `test_the_mockup_iframe_shows_at_display` in `tests/factory_dashboard/test_proposal.py`, and into `test_the_dock_is_compact_on_a_phone` and `test_the_review_status_shows_after_sending_on_a_phone` in `tests/factory_dashboard/test_thread.py`. Follow `_f6_adr_plan_merge` in `test_proposal.py` (a helper with a one-line docstring that sets up F6's thread).
- Add `_f6_mockup_review(db_path: Path, planning: int, checkout: Path) -> None` to `test_proposal.py`, beside `_f6_adr_plan_merge`, docstring: `"""F6's thread lists a mock-up proposal whose file is on ``plan/f6``."""`. Its body is those twelve lines.
- Use it in the four tests above. `test_thread.py` imports `_f6_mockup_review` instead of `_REVIEW_MOCKUP` and `ADR_ON_MAIN`, if it no longer uses them.
- Leave `test_the_mockup_route_serves_the_plan_branchs_mockup_and_nothing_else` as it is: it also commits the card f6-planning-room.md, which its refused paths need.
- **Change only the setup: no assertion, viewport or test name changes.**

### Done when
- the four tests call `_f6_mockup_review` and none of them runs `git(checkout, ...)` itself
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2641
gate_failures: []
tokens: 681304
```

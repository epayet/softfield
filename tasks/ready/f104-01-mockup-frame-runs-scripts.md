---
id: f104-01-mockup-frame-runs-scripts
milestone: f104-mockups-act-like-i-can-interact
depends_on: [f42-01-review-page-room]
agent: lead
difficulty: 2
files:
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A mock-up's scripts run in the review page's frame, so its buttons and tabs answer there, and it still can't act as the dashboard.

### Context
Read F104's Decisions D1–D3 in `docs/milestones/f104-mockups-act-like-i-can-interact.md`, the `#mockup` iframe in `factory_dashboard/templates/proposal.html`, `def mockup_file` in `factory_dashboard/planning.py`, and in `tests/factory_dashboard/test_planning.py` `test_the_mockup_route_serves_the_plan_branchs_mockup_and_nothing_else` (the plan branch with a mock-up on it) and `_open` (a page in Chromium answered by the test client).
- The owner (2026-10-10): "Mockups act like I can interact with but I can't, f54 is blocked because of that". The iframe's bare `sandbox` turns scripts off; the route's own CSP (`sandbox allow-scripts`) already allows them.
- D1: the iframe's attribute becomes `sandbox="allow-scripts"`, no other token. Change nothing in `factory_dashboard/planning.py` or `factory_dashboard/requests.py`.
- f42-01 has changed these lines before you (a link, the frame hidden under 640 px): keep what it did, and test at a width where the frame shows.
- `_open` answers every request as `text/html` without the route's headers: the frame's own attribute is what the browser test checks.
- Test first: write the browser test, see it fail on the bare `sandbox`, then change the attribute.

### Done when
- in Chromium at 1024 px, a mock-up whose script writes a word into its page shows that word inside the review page's frame
- in that frame the script's own origin is `"null"`, and reading `parent.document` throws
- the page's iframe carries exactly `sandbox="allow-scripts"`: a test fails on a bare `sandbox` and on any other token (`allow-same-origin`, `allow-forms`, `allow-popups`, `allow-top-navigation`)
- the route's `Content-Security-Policy` is unchanged (the existing check)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

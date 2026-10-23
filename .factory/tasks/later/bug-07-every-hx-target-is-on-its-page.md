---
id: bug-07-every-hx-target-is-on-its-page
milestone: bugs
difficulty: 5
depends_on: []
area: factory
priority: 30
finding: f159-there-s-a-bug-set-aside-F4
tests_only: true
files:
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
One dashboard test fails whenever a button's `hx-target` names an element its page doesn't have.

### Context
f159-01's Queue it button pointed `hx-target` at an element that existed only once the request was sent, so htmx sent nothing (it refuses a request whose target is missing), and every test passed: they read only the markup. The code is right today; this is the missing guard.
- Read the fixtures at the top of `tests/factory_dashboard/test_app.py` and `tests/factory_dashboard/conftest.py`, and how `tests/factory_dashboard/test_tickets.py` builds a `later` ticket, for the data each page needs.
- The pages: `/tickets/<a later ticket>`, `/tickets`, `/board`, `/planning`, a card's thread (`/planning/<key>`), `/milestones/<key>`.

### Done when
- for each of those pages, every `hx-target="#x"` names an element with `id="x"` on the same page, or is `this`, or starts with `closest `, `next `, `previous ` or `find `
- the test names the page and the missing id when it fails
- a page rendered with a made-up `hx-target="#nowhere"` fails the check (a small case on a literal string, so the check itself can fail)
- all gates pass (see `docs/workflow.md`)

---
id: f9-36-fix-lead-next-link-test
milestone: f9-line-polish
difficulty: 2
depends_on: []
files:
  - tests/factory_dashboard/test_line.py
tests:
  - tests/factory_dashboard/test_line.py
finding: f9-line-polish-F3
tests_only: true
---

### Goal
The test of the idle lead's "next:" link measures the link's own text against the lead machine's box, not a box the test works out itself.

### Context
Read `machine` in `factory_dashboard/static/factory.js` (the idle lead draws a link to its next ticket under its plate) and `test_idle_lead_next_ticket_text_lies_inside_lead_machine_rect` in `tests/factory_dashboard/test_line.py`.
- Today the test's `expected` compares two boxes it computes from constants, so it is always true, and `actual` measures `svg.querySelector('[data-machine] text')`, the first text of the first machine ("THE LEAD"), not the link.
- The code is right: change only the test.

### Done when
- the test finds the lead machine by its `data-machine` id, takes the text inside its `a` (the one reading "next: …") and its widest `rect.unit` (the machine's body; the first one is its chimney), and asserts the text's box lies inside that rect's box, from `getBoundingClientRect` of both
- it would fail if the link's text were drawn at (0, 16), as before f9-33
- no assertion compares boxes the test computes from constants
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass (see `docs/workflow.md`)

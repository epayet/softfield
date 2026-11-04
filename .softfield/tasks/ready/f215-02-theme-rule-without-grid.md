---
id: f215-02-theme-rule-without-grid
milestone: f215-i-m-not-a-fan-of
agent: lead
difficulty: 1
depends_on: [f215-01-floor-without-grid]
files:
  - runner/instructions/author/owner.md
  - .softfield/cards/f81-assess-the-current-ui-state-of.md
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The factory theme's rule stops naming a grid, so new pages and mock-ups don't bring it back.

### Context
The owner, 2026-11-04, on `.softfield/cards/f215-i-m-not-a-fan-of.md`: "I'm not a fan of the grid like background".
- `runner/instructions/author/owner.md`, the "Factory theme" preference: take "and a faint grid" out of the list of the theme's parts, and "grid" out of the "Ornament never looks like a status" line. Add `(owner, 2026-11-04: no grid on the floor, F215)` to the first of these. Keep the sentence's other parts.
- `.softfield/cards/f81-assess-the-current-ui-state-of.md` D3: replace its last sentence ("The faint 32 px grid on the floor is `--grid`.") with one saying F215 removed the grid from the floor. Leave its ticket table as it is: it records what was built.

### Done when
- neither file presents a grid as part of the theme for new work
- no test is added: this is wording, and `tests/factory_dashboard/test_app.py` (from f215-01) already holds the page; it still passes
- all gates pass (see `docs/workflow.md`)

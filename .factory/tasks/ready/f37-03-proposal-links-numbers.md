---
id: f37-03-proposal-links-numbers
milestone: f37-in-planning-mode-it-tends-to
difficulty: 3
depends_on: [f37-02-thread-links-numbers, f67-02-key-points-by-kind]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A proposal's review page links and names the numbers in its key points, as its thread does.

### Context
The picture to build: `.factory/cards/f37-mockup/thread-names.html` (Proposed); the review page draws the same links. Read `.factory/cards/f37-in-planning-mode-it-tends-to.md` D2 and D3, the function f37-02 added in `factory_dashboard/planning.py` (reuse it, don't copy it), and the key points' title and text in `factory_dashboard/templates/proposal.html`.

### Done when
- a key point whose text says `F42` and `f15-06-card-actions` shows them as links, F42 with its name, on the proposal's review page
- a key point with neither shows as before
- the layout check passes at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

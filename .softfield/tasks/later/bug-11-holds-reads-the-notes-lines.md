---
id: bug-11-holds-reads-the-notes-lines
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 35
finding: f48-F2
files:
  - runner/planner.py
tests:
  - tests/runner/test_planner.py
---

### Goal
A short note planted under a card's title is written to the card, not taken as "planted already".

### Context
Read `def holds`, `def _notes` and `def seed_card` in `runner/planner.py`. `runner/**` is protected: tests first.
- `holds` looks for the note's title and thoughts anywhere in the card's doc, as substrings: a note "ok" under a taken title reads as planted already, and is lost.
- Match the thoughts within the doc's `## Notes` section, on whole lines (whitespace collapsed, as now).

### Done when
- a note "ok" on a card whose doc has "ok" only inside another word or outside `## Notes` is written
- the same note planted twice is held the second time, as today
- a cut title's ellipsis still doesn't count (the existing case keeps its assertion)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

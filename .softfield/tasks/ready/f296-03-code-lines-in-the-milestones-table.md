---
id: f296-03-code-lines-in-the-milestones-table
milestone: f296-show-each-milestone-s-net-code
difficulty: 1
depends_on:
  - f296-02-code-lines-on-the-milestone-page
agent: developer
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestones.html
  - tests/factory_dashboard/test_milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The Milestones table has a "Code lines" column: each milestone's net code lines, so milestones can be compared side by side.

### Context
Read `.softfield/cards/f296-show-each-milestone-s-net-code.md` (D3, D4). The picture to build is `.softfield/cards/f296-mockup/code-lines.html`, "Milestones", Proposed.
- `code_lines(conn, project)` in `factory_dashboard/queries.py` gives each milestone's (added, removed).
- The table's rows are built by `milestones_list` in `factory_dashboard/milestones.py` (its row has `claude_dollars`) and drawn in `factory_dashboard/templates/milestones.html`.

### Done when
- a "Code lines" column sits after "Claude $", right-aligned like the other numbers
- a milestone with tickets +92 −13 reads "+79"; one below zero reads "−40"; one with nothing counted reads "–"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

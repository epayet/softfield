---
id: f9-33-fix-lead-next-link-position
milestone: f9-line-polish
depends_on: []
difficulty: 2
finding: f9-23-F1
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The idle lead's next-ticket link sits on the lead's machine, on the line where `next: …` used to be, and still says it is the next ticket.

### Context
In `factory_dashboard/static/factory.js` `machine`, the idle lead branch draws the link's text at `(0, 16)`, absolute SVG coordinates, not at `left, line` like every other line of the machine (f9-23). The text lands in the floor's top-left corner, away from the lead, and the `merged today` line under it no longer lines up. The `next:` label was also dropped, so the bare ticket id no longer says what it is. `g.appendChild(link)` repeats what `make_link(g, …)` already did.
- The f9-23 tests (`test_idle_lead_says_next_ticket`, `test_idle_lead_with_merges_shows_next_ticket_and_merge_count`) check the text and the `href`, not where the text is drawn.

### Done when
- the link's text is drawn inside the lead machine's box, at the old `next:` position, and its words say it is the next ticket
- a test checks the text's bounding box lies inside the lead machine's `rect`
- the `merged today` line still sits right under it
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f9-23-floor-taps
milestone: f9-line-polish
depends_on: [f9-22-floor-words]
difficulty: 3
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
Everything named on the floor opens what it names: merged crates, the lead's next ticket, the harvest stash's tiles, Planting and the ripe milestones. The stash's tiles fit their words.

### Context
Read in `factory_dashboard/static/factory.js` `merged`, `stash`, `ripe`, `planting`, `machine` (the lead's `next:` line), `make_link` and how `seeds` and `rows` use it (f9-03, the pattern to follow), and the crate card (`crateInfo`, `showCard` and the click listener on `[data-crate]`). Then the floor tests in `tests/factory_dashboard/test_line.py`.
- The owner (2026-10-06): "I can't click merged tickets today", "the lead says what the next ticket is but it's just text, can't click on it", "harvest stash: text overflows a lot out of the boxes".
- Merged crates carry `data-merged`, not `data-crate`, so the card never opens for them. `crateInfo` already looks in `doc.merged`.
- A stash tile is 52 px wide and shows the whole key (`F7-FACTORY-FIXES` overflows). It should show the short key (`F7`, the part before the first `-`) with the full key and title in its `<title>`.
- Links keep the page's `?project=` as `seeds` does. Where: the lead's next ticket → `/tickets/<id>`; a stash tile and a ripe line → `/milestones/<key>`; Planting → `/planning`.

### Done when
- tapping a merged crate opens the crate card with its ticket's link
- the lead's `next:` line is a link to its ticket's page
- each stash tile shows only its short key, inside its 52 px, and links to its milestone; its title holds the full key
- Planting links to `/planning`, and each ripe line links to its milestone
- every link keeps `?project=`, and the layout check passes at 390 px and 1440 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3246
gate_failures: []
tokens: 3135625
```

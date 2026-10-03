---
id: f3-12-phone-floor
milestone: f3
depends_on: []
agent: lead
difficulty: 6
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On a phone, the line looks like the phone mock-up: the whole floor drawn top to bottom with its plants, crates, belts and counts, every label readable, nothing overlapping.

### Context
Read `docs/milestones/f3-line-mockup/LinePhone.dc.html` (the picture: its SVG and its script's data), `factory_dashboard/static/factory.js` (`drawPhone`, `PHONE`; the desktop `draw` does each piece right) and the phone tests in `tests/factory_dashboard/test_line.py`.
- **What the owner sees today (2026-10-03, 390 px):** after the lead's colour fix, the phone floor shows outlines only:
  - no planting unit and no planted rows (the desktop has both);
  - an empty queue hopper (no crates);
  - few belts;
  - an empty harvest stash;
  - cut-off names ("SONNET" and "COPIL…" squeezed into 70 px boxes);
  - "DEVELOPER BAY" under a chimney;
  - the ripe icon over "RIPE".
- **Draw every station the desktop draws,** in the mock-up's portrait layout:
  - the field with seeds, the planting unit and the rows' plants with their counts;
  - the queue's crates (the first six in run order);
  - the lead full width;
  - the two reviewers side by side at about 160 px each;
  - the developer bay's machines with their working crates;
  - checks, with the retry belt;
  - merged and ripe;
  - the stash's crates.

  Every belt between them goes top to bottom, carrying and counted as on desktop. Reuse the desktop's drawing helpers rather than copying them.
- **Take screenshots at 390 px,** dark and light, before and after, and attach them to the job's notes (the review reads them).

### Done when
- at 390 px, every station of the document is drawn, the queue holds crates and the stash its milestones (browser test)
- no two text labels' boxes overlap, and no label overflows its station's box (a browser test over the text elements' bounding boxes)
- the colours test still passes (no black fills)
- `uv run runner check-all --task f3-12-phone-floor` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

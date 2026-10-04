---
id: f3-22-line-look-review
milestone: f3
depends_on: [f5-14-factory-look, f3-21-since-you-looked, f4-34-fix-now-first-legend-untested, f4-35-fix-crate-card-untested-unescaped]
agent: lead
difficulty: 4
files:
  - docs/milestones/f3.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
Look at the factory line again next to the new global look (f5-14), and propose what would improve it, as tickets the owner can pick from at F3's sign-off.

### Context
Read `docs/milestones/f3.md` (D11 and "Owner's notes, 2026-10-03"), the tickets f5-14-factory-look and f3-17 to f3-21 (in tasks/done/ by then), and the pictures: `docs/milestones/f3-line-mockup/Line.dc.html`, `docs/milestones/f3-line-mockup/LinePhone.dc.html`, `docs/milestones/f1-factory-mockup.html` and the board mock-up `docs/milestones/f5-board-mockup/Main.dc.html`.
- **Why (owner, 2026-10-03):** first the small line fixes, then the global redesign, "and then review once more the factory line design to see if improvements could be made alongside the global redesign".
- **Look at the real page:**
  - Run the dashboard on a copy of the metrics database, the way the browser tests in `tests/factory_dashboard/test_line.py` do.
  - Take screenshots of `/` at 1440 px and at 390 px wide, dark and light, and save them under `var/shots/f3-22/`.
  - Compare them with the mock-ups: the floor, the machines, the belts, Now, "While you were away", and how the line sits in the new look (tokens, fonts, top bar).
- **Write, don't build.** Each improvement worth making becomes a developer ticket in `tasks/later/` (one concept each, with the picture it follows), not in `ready/`: the owner chooses at sign-off.
- Add a section "Line look after the redesign" to `docs/milestones/f3.md`: one line per proposed ticket (what the owner would notice), and the screenshots' paths.
- Change no code.

### Done when
- the section is in `docs/milestones/f3.md`, with a line for each proposed ticket
- each proposed ticket is in `tasks/later/` and passes pre-flight (`uv run pytest -q tests/runner/test_tasks.py`)
- all gates pass

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

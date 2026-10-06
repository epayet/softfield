---
id: f9-22-floor-words
milestone: f9-line-polish
depends_on: []
difficulty: 4
files:
  - factory_dashboard/templates/_partials/line.html
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/overview.html
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The floor says what its marks mean without being asked. Belt numbers say "today", Planting says what it is, the developer bay is blue, the legend explains the faded crates, and the refresh note goes.

### Context
Read `factory_dashboard/templates/_partials/line.html` (the heading and "How to read the floor"), in `factory_dashboard/static/factory.js` `belt` (its `words`) and `planting`, the `.floor` colour rules in `factory_dashboard/static/dashboard.css` (`.floor .developers`, `.floor .crate.developer`, `.floor .crate.waits`, `.swatch.developer`, the theme tokens at the top), the `#savings` heading in `factory_dashboard/templates/overview.html`, and the floor tests in `tests/factory_dashboard/test_line.py`.
- The owner's questions (2026-10-06), each answered on the floor itself:
  - "Refreshes every 5 s, is that true? I don't need to see it": drop the heading's "live · refreshes every 5 s" (the Now panel keeps its own).
  - "What do the numbers next to the lanes mean?": a belt's words become "developer · 7 today". On the phone, where a belt shows a bare number, it becomes "7 today" (short belts keep the bare number). A replay counts its own day, and the legend says so.
  - "What's supposed to be in planting?": the cards the owner is planning with the lead (open planning-room threads). Its words become "ideas you're planning / with the lead", and the count "N in talks".
  - "The checks' green dot is a similar colour to the developer bay; make the developer bay more blue": a new floor token for developers (the bay's frame, its machines, developer crates, the legend's swatch), blue in both themes and clearly different from `--good` and from the lead's orange. Charts keep `--a3`.
  - "Why are the developer tickets dotted?": a faded, dashed crate is a ticket waiting on another ticket (`.crate.waits`), whatever its colour. The legend adds "faded, dashed: waits for another ticket".
  - "Is the savings from delegating on the replay's timescale?": no, it's the current milestone's total. Its heading says "so far on F6" (the milestone's key) rather than ", F6".

### Done when
- the floor's heading has no "refreshes"; the Now panel still says it
- with a belt counted 7 today, its words end with "7 today" on desktop and on the phone (on the phone, where it isn't a short belt)
- Planting reads "ideas you're planning", "with the lead" and "N in talks"
- a developer crate's computed fill is not the checks light's fill, nor the lead crate's, in both themes
- the legend names the faded, dashed crates and says a replay counts its own day
- the savings heading names the milestone with "so far"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

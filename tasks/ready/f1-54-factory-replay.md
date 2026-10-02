---
id: f1-54-factory-replay
milestone: f1
depends_on: [f1-53-factory-line]
difficulty: 7
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/line.html
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The factory line replays its milestone: Play and the step buttons move from one event to the next, and each crate travels along the belts of its trip.

### Context
Read `docs/milestones/f1.md` D10 ("What the page shows"). Follow the worked example f1-53 built: `factory_dashboard/line.py` (the document; every trip is `{at, crate, belts, to}`), `factory_dashboard/static/factory.js`, `factory_dashboard/templates/line.html` and its browser tests in `tests/factory_dashboard/test_line.py`. Open `docs/milestones/f1-factory-mockup.html` in a browser to see the result; don't read it as code.
- **Controls under the floor:** a slider over the milestone's time, Play / Pause, ◀ and ▶ (previous and next event), and a speed: one event every 5, 3 (default) or 1.5 s. Dragging the slider jumps; Play and the step buttons animate.
- **A trip:** the crate glides along its belts' points in order (about 1–2.5 s), then to its place; each belt it uses rolls while the crate is on it and only then.
- **The Checks gate** flashes green when a crate leaves on `checks→merged`, red on `checks→dev` or `checks→lead`.
- **The working ticket's path:** the belt it came on solid, its way on to Merged dashed (D10).
- **Smoke:** a working machine smokes from its chimney (bigger for a higher rating), driven from JavaScript so phones animate it; with `prefers-reduced-motion: reduce`, still puffs and no gliding.
- **No rule in JavaScript:** where a crate goes and when comes from the document only.

### Done when
- ▶ from the start moves the time to the first event and the crate to where that trip puts it; ◀ goes back
- during a trip, each of its belts has the rolling state, and none after it ends
- a crate whose trip is `checks→dev` turns the gate red; `checks→merged`, green
- with reduced motion, crates jump to their place and the smoke is still
- the listed `tests:` pass, and fail without the change (browser tests, as f1-53's)
- all gates pass (see `docs/workflow.md`)

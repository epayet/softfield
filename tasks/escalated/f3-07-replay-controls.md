---
id: f3-07-replay-controls
milestone: f3
depends_on: [f3-06-replay-data, f3-03-line-motion, f3-09-line-phone-fixes, f3-10-line-phone-finish]
difficulty: 5
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/templates/line.html
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On the factory line, "Replay overnight" plays what happened since the owner last looked: the floor steps from event to event, with Play, ◀ ▶, a speed and the time, on desktop and phone.

### Context
Read the replay controls and the sticky phone bar in `docs/milestones/f1-factory-mockup.html` (the picture: `.replay`, `.play`, the steps and speeds), `factory_dashboard/line.py` (`replay`, f3-06), `factory_dashboard/static/factory.js` (the floor and its motion, f3-01 to f3-03) and the browser tests in `tests/factory_dashboard/test_line.py`.
- **Data:** a "Replay" button loads `/line/replay?since=…&until=…` (f3-06 built this JSON route; `until` defaults to now). The default is the "overnight" preset: its URL is already in the page, on `.page` as `data-replay` (`/line` reads and then updates the `line_seen` cookie). A picker offers the last 24 h or a run. Each event's fields are in `replay`'s docstring.
- **It must look like the line moving** (owner, 2026-10-03), not a list of events: crates travel their trips' belts between stations, belts roll while they carry, machines light up and smoke while they work, the checks light flashes. Reuse the F1 mock-up's motion (`docs/milestones/f1-factory-mockup.html`) and f3-03's classes.
- **While replaying:**
  - the live refresh pauses;
  - each step moves the crates along their trips' belts and updates the machines, checks and counts (with f3-03's motion);
  - a readout gives the event's time and one line in words ("03:12 f4-06 failed checks: ruff");
  - "Back to live" resumes the refresh.
- Speeds: an event every 5, 3 or 1.5 s. ◀ ▶ step by hand. Under 640 px the controls are a sticky bar at the bottom.

### Done when
- a browser test on a fixture night: Play steps through the events in order and the readout shows each one's time and words; ◀ goes back one; "Back to live" restores the live floor
- the phone layout shows the sticky bar, with every control at least 44 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 562968
logs: var/runs/20261003-074205/f3-07-replay-controls
```

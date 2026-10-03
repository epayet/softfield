---
id: f3-07-replay-controls
milestone: f3
depends_on: [f3-06-replay-data, f3-03-line-motion]
difficulty: 5
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/templates/overview.html
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On the Overview, "Replay overnight" plays what happened since the owner last looked: the floor steps from event to event, with Play, ◀ ▶, a speed and the time, on desktop and phone.

### Context
Read the replay controls and the sticky phone bar in `docs/milestones/f1-factory-mockup.html` (the picture: `.replay`, `.play`, the steps and speeds), `factory_dashboard/line.py` (`replay`, f3-06), `factory_dashboard/static/factory.js` (the floor and its motion, f3-01 to f3-03) and the browser tests in `tests/factory_dashboard/test_line.py`.
- **Data:** a "Replay" button loads `/line/replay?since=…&until=…` (a JSON route in `factory_dashboard/overview.py`, read-only). The default is the "overnight" preset; a picker offers the last 24 h or a run.
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

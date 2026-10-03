---
id: f3-06-replay-data
milestone: f3
depends_on: [f3-04-clog-today]
agent: lead
difficulty: 6
files:
  - factory_dashboard/line.py
  - factory_dashboard/queries.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The line's document can be built for any moment and any stretch of time, so the owner can replay what happened overnight.

### Context
Read `docs/milestones/f3.md` D10 (the trips, idle stretches over 40 min) and D11, `factory_dashboard/line.py` (`live_line`, the trips; f3-01 and f3-04) and the replay controls of `docs/milestones/f1-factory-mockup.html` (Play, step, the speeds, the time readout). Test-first.
- **`line.replay(conn, project, since, until)`:** the line's document at `since`, then every event up to `until` in time order:
  - a trip `{at, crate, belts, to}`;
  - a machine changing state;
  - a check passing or failing;
  - a card changing stage;
  - a limit starting or ending.

  `factory_dashboard/static/factory.js` (f3-07) only steps through it.
- **`live_line(..., at=None)`** gives the document at any past moment: the same rules, from the jobs and runs whose times cover `at`.
- **Idle stretches** over 40 min become one event with their real length (D10), so a night replays in minutes.
- A preset for the owner: "overnight" is from the last time the dashboard was opened (a cookie the page sets, or 20:00 yesterday) until now.

### Done when
- for a fixture night (a merge, a failed attempt, a park at a limit, a 3 h idle stretch), the events come out in order, the idle stretch is one event, and the document at each event's time matches `live_line(at=…)`
- `live_line(at=t)` at a moment mid-job shows that job's machine working
- `uv run runner check-all --task f3-06-replay-data` passes

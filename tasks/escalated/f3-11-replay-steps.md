---
id: f3-11-replay-steps
milestone: f3
depends_on: [f3-07-replay-controls]
difficulty: 7
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
In a replay, the floor steps from event to event like the line moving: Play steps at the chosen speed, ◀ ▶ step by hand, and the readout gives each event's time and one line in words ("21:40 n1-02-retry failed checks: ruff").

### Context
Read `factory_dashboard/static/factory.js` (f3-07's replay bar and the JSON it keeps, `draw`, `drawPhone`, the checks light in `drawAll`), the event fields in `replay`'s docstring in `factory_dashboard/line.py`, `brief` and the browser tests (`open_line`, `night_client`, `night_db`) in `tests/factory_dashboard/test_line.py`, and the mock-up's `step` and `jump` in `docs/milestones/f1-factory-mockup.html`.
- **Each step is a document:** step n is the JSON's `line` with events 1 to n applied in turn to a copy (`structuredClone`), then drawn with `draw`, or `drawPhone` under 640 px. Leave `line` itself untouched, so ◀ can rebuild from it.
- **The document's fields an event touches:** `queue` (crates waiting), `machines` (`state`, `crate`, `reset`), `belts` (`carrying`, `today`), `merged` and the station counts in `stations`. A `machine` event names only the ticket; a machine's `crate` is `{ticket, title, kind, role, attempt, minutes}`, and the crate's title and kind are on its entry in `queue` (or wherever the crate last was). `card` and `idle` events change only the readout.
- **Motion comes with the document:** `draw` already gives a carrying belt `carrying moving`, and a working machine `on` and its smoke (f3-03). A `check` event flashes the checks light: `flash-green` when passed, `flash-red` when failed.
- **The readout:** one line per event, saying what `brief` says in words. Its clock is the event's `at` string's HH:MM (characters 11 to 16), never a `Date`, which would shift it to the browser's zone.
- **Speeds:** the speed select's value is the milliseconds between steps. Play stops at the last event; ◀ and ▶ stop playing.
- **Tests:** `/line` builds `since` in the server's local zone, so build the expected readouts from the route's JSON (each event's clock and crate or machine), never from fixed clocks. A test can pick the fastest speed and wait for the readout to change.

### Done when
- a browser test on the fixture night: ▶ steps through the events in order and the readout shows each one's clock and crate or machine; ◀ goes back one; Play steps on its own; "Back to live" restores the live floor
- after the first `machine` event that sets a machine working, that machine is drawn `on` with the crate's ticket; after the failed check (`n1-02-retry`, ruff) the light flashes red
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 4294026
logs: var/runs/20261003-150632/f3-11-replay-steps
```

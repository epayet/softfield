---
id: f199-02-strip
milestone: f199-let-s-improve-the-factory-floor
agent: lead
difficulty: 3
depends_on: []
files:
  - factory_dashboard/line.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/templates/_partials/strip.html
  - factory_dashboard/static/dashboard.css
  - .softfield/tasks/ready/bug-57-a-developer-ticket-keeps-to-one-page.md
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
Bring the strip that an escalation already built onto main: the Overview shows the floor as a strip under Now and the Queue, with one belt, six stops, one line saying what runs, and a button to open the map.

### Context
The work is done and passed `softfield check-all` (4,079 tests) on 26 Nov. It is the one commit on the branch escalation/f199-02-strip, 516a845c. It never reached main only because the escalation, resumed after Claude's 5-hour limit, wrote its decision to the wrong run folder. Read it with `git show 516a845c`, then write the same changes into main's files as they are now. Don't build it again.
- What it holds: `glance()` in `factory_dashboard/line.py`, `factory_dashboard/templates/_partials/strip.html` under Now and the Queue, refreshed by `/live` through `hx-select-oob` (`factory_dashboard/templates/_partials/live.html`, `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html`), the strip's CSS, 6 unit tests and 6 browser tests in `tests/factory_dashboard/test_line.py`, and two Overview tests updated in `tests/factory_dashboard/test_overview.py`.
- It also added one line to the bug-57 ticket in the ready folder, a fourth case for the developer-routing check. If that ticket is still in the ready folder, add the line; if it has run, leave it.
- Where main has moved since, keep main's change and fit the strip around it. The picture remains Proposed in `.softfield/cards/f199-mockup/floor.html`, and the shape of `glance` is D6 in `.softfield/cards/f199-let-s-improve-the-factory-floor.md`.

### Done when
- `glance` on a document with Opus working on a planner job: its status words name Opus and the job; on a document with a `wait`: the wait's words, kind `clog`; with nothing running: "nothing is running"
- `glance`'s result holds no card or ticket title
- at 390 px wide: the strip is at most 200 px tall, all six stops in one row, nothing cut off, each stop at least 44 px wide; at 1440 px the same six stops in one row
- a tap on a stop or on "Open the map" goes to `/floor`; the strip's status changes without a reload when `/live` brings a new job
- light and dark themes both readable
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 456358
logs: .softfield/var/runs/20261126-001843/f199-02-strip
```

```yaml
# --- runner ---
result: blocked
reason: the escalation ended with no decision; its work is on escalation/f199-02-strip
```

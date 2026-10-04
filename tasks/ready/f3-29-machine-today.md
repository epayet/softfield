---
id: f3-29-machine-today
milestone: f9-line-polish
depends_on: []
difficulty: 4
files:
  - factory_dashboard/line.py
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
An idle machine says what it did today ("3 merged today"), and the idle lead says which ticket it takes next, so a quiet floor still tells a story.

### Context
Read `live_line`, `_machines`, the `Trip` and `Job` dataclasses in `factory_dashboard/line.py`, `machine` in `factory_dashboard/static/factory.js` (desktop and phone), and the document and browser tests in `tests/factory_dashboard/test_line.py`. The picture: `docs/milestones/f3-line-mockup/Line.dc.html`, the lead ("idle: one job at a time", "next: f4-03 requeue pre-flight") and GPT-OSS-120B ("idle: one job", "3 merged today").
- **What the review saw (f3-22, `var/shots/f3-22/desktop-1440-dark-line-live.png`):** every idle machine reads only "idle", with a large empty box under it.
- **The data, in Python** (`docs/milestones/f3.md` D11): each machine in the document gains `merged_today`, the number of today's trips (since local midnight, up to `at`) that end at `merged` and whose `job` ran on that machine's agent. A machine with none has 0.
- **The drawing:** an idle machine shows "N merged today" under "idle" when N > 0. The lead, idle, shows "next: <ticket>" for the first crate of the queue that is a lead ticket, when there is one.
- **Idle looks idle** (owner, 2026-10-04: "the idle factories could be a bit more obvious that they're idle"): an idle machine's body is drawn dimmed (a class `idle` on its group, styled in `factory_dashboard/static/dashboard.css`), with no lights lit and no smoke.
- A working machine is unchanged. Desktop and phone both, with no label overlapping (the phone's label test must still pass).

### Done when
- a document test: a developer agent that merged two tickets today and one yesterday has `merged_today` 2; an agent with none has 0
- a browser test: an idle machine with merges today shows "merged today" with its count; the idle lead shows its next lead ticket
- a browser test: an idle machine's group has the class `idle` and a working one hasn't
- the phone label test still passes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f9-01-line-shows-waits
milestone: f9-line-polish
depends_on: []
agent: lead
difficulty: 4
priority: 1
files:
  - factory_dashboard/line.py
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
While the runner waits instead of working (for Claude's reset, for the owner, behind a parked job, or with nothing runnable), the floor shows it clogged, at the machine it waits for, with words that say on what and until when.

### Context
Read `_machines` in `factory_dashboard/line.py` (today `waiting` means only an agent at its limit), `machine` and `machines` in `factory_dashboard/static/factory.js`, the `--clog` colour in `factory_dashboard/static/dashboard.css`, and `set_activity` in `runner/loop.py`: the run's `activity` and `waiting_until` (the `runs` table) say what the runner is doing and until when. The picture: `docs/milestones/f3-line-mockup/`. Test-first.
- The owner (2026-10-04): "factory line doesn't [look] clogged when it's waiting on something".
- One clog at a time: the machine named by the wait (Claude's for a reset or a parked Claude job, the lead's desk for the owner), or the queue when nothing is runnable. Its words: "waiting for Claude's reset · 21:50", "waiting for you: sign off F5", "nothing ready: F5's next tickets wait on f5-07".
- Reduced motion: the sign, without animation.

### Done when
- a document test per kind of wait gives the clog's machine and words; a working runner gives none
- a browser test: the clog sign and its words show on desktop and phone
- `uv run runner check-all --task f9-01-line-shows-waits` passes

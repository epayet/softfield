---
id: f1-53-factory-line
milestone: f1
depends_on: []
agent: lead
difficulty: 8
files:
  - factory_dashboard/line.py
  - factory_dashboard/queries.py
  - factory_dashboard/app.py
  - factory_dashboard/templates/line.html
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/conftest.py
  - docs/agents/developer.md
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_queries.py
---

### Goal
`/milestones/<key>/line` shows a milestone as a factory floor at one moment, from a JSON document that holds every rule, so the developers' tickets after it only animate and lay it out.

### Context
Read `docs/milestones/f1.md` D10 (all of it: it is the contract for f1-54 to f1-58) and D5. Look at `docs/milestones/f1-factory-mockup.html` in a browser, not as text: it is the picture (v18), with the trip rules in its `transits` and `locate` functions as a sketch, not code to copy. Read `factory_dashboard/overview.py` (the worked example), `factory_dashboard/timeline.py`, `factory_dashboard/queries.py`, `runner/tasks.py` (`pick_next`), `runner/config.py` (`load_config`) and `runner/metrics.py` (the tables).
- **`queries.run_order(conn, project)`:** the `ready` tickets in the order the runner will take them (`pick_next` applied repeatedly), each with "ready now" or the tickets it still waits for.
- **`line.factory_line(conn, project, milestone)`:** D10's document: machines (from the project's `workflow/runner.toml` via `load_config` on `projects.repo`, plus agents seen in jobs; a missing or unreadable repo falls back to the jobs alone, ratings unknown), tickets (kind, deps, state, run order, jobs), every trip `{at, crate, belts, to}`, each belt's last and next trip, limit windows from `usage_events`, and the idle stretches over 40 min.
- **The page:** the wide floor at a moment chosen by `?at=` (default: the last event): stations, named belts with direction chevrons, crates where the trips put them, the developer bay, the lead with its model plates, rating gauges, LOCAL/CLOUD plates, the Checks gate; a side panel (time, working now, up next in run order, latest jobs); hover on a crate shows its details and outlines its dependencies. `factory_dashboard/static/factory.js` draws from the JSON only.
- **A browser test pattern for the dashboard** (none exists): in `tests/factory_dashboard/test_line.py`, render the page with `TestClient`, open it in pytest-playwright's `page` with `/static/` served from disk (`page.route`), as `tests/browser/conftest.py` does for Coucou's files, and assert on what is drawn (one crate per ticket, where the JSON puts it). f1-54 to f1-58 test their behaviour this way.
- **Worked example:** add "Factory line" to the worked examples in `docs/agents/developer.md` (data in Python, drawing in `factory_dashboard/static/factory.js`, tests on the JSON and one browser test), keeping the file within its 15 notes.

**The dashboard is English-only and never writes the database.**

### Done when
- `run_order` on the fixture gives the order `pick_next` would, with each ticket's waits
- for a fixture milestone with a developer ticket that fails once, gets a direction and passes, the trips are queue→dev, dev→checks, checks→lead, lead→dev, dev→checks→merged, in time order
- a lead ticket parked by a limit goes lead→queue and comes back on queue→lead; a checkpoint job goes merged→lead→queue
- the lead is one machine with a plate per Claude model; a shadow agent is its own machine; a project whose repo can't be read still renders
- `/milestones/f1/line` renders, with the document in its JSON block, and `?at=` moves the crates
- a browser test opens the page and finds a crate per ticket at its station
- `uv run runner check-all --task f1-53-factory-line` passes

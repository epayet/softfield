---
id: f3-01-factory-line
milestone: f3
depends_on: [f4-16-allowance-mark, f4-14-keep-selection, f5-10-five-hour-buttons, f5-11-queue-priority, f5-14-factory-look, f5-15-board-data]
agent: lead
difficulty: 8
files:
  - factory_dashboard/line.py
  - factory_dashboard/queries.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/conftest.py
  - docs/agents/developer.md
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_queries.py
---

### Goal
`/` shows the factory line live: the field, the queue, the lead, the reviewers, the developer bay, checks, merged, ripe and the stash, drawn from one Python document that holds every rule. It's the worked example the rest of F3 builds on.

### Context
**Continue your branch** (`task/f3-01-factory-line`, started as f1-53): `factory_dashboard/line.py` (the trips), `queries.run_order` and their tests exist, written for D10's replay page. Main has moved a lot since (F4, F5), so merge main in first. Keep the trips (D11's belt counts come from them, and replay will need them later), and drop what only `/milestones/<key>/line` needed.

Read `docs/milestones/f3.md` D11 (all of it: it's the contract for 02–05), the line mock-up (`docs/milestones/f3-line-mockup/Line.dc.html` and `docs/milestones/f3-line-mockup/LinePhone.dc.html`: read the SVG and the data in each file's script, not pages to open), `factory_dashboard/board.py` (the field's cards, f5-15), `factory_dashboard/overview.py` (the live partial since F4 and F5) and `runner/config.py` (`load_config`, for the roles).
- **`line.live_line(conn, project, now)`:** D11's document: stations, machines with their state and crate, belts with today's count and `carrying`, Now, and the next three in run order. A project whose repo can't be read falls back to the agents seen in jobs.
  - The clog numbers are f3-04's: leave them out of this ticket's document, but give the document a `clog` key holding `None`.
- **The drawing:** `factory_dashboard/static/factory.js` draws the desktop floor as hand-written SVG from the document in the live partial's JSON block (D5 style). It draws with the f5-14 tokens and has no rules of its own. Under 640 px it shows a short note until f3-02.
- **Browser tests** (none exist for the dashboard yet): in `tests/factory_dashboard/test_line.py`, render with `TestClient`, open it in pytest-playwright's `page` with `/static/` served from disk (`page.route`, as `tests/browser/conftest.py` does), and assert on what's drawn.
- Add "Factory line" to the worked examples in `docs/agents/developer.md` (data in Python, drawing in `factory_dashboard/static/factory.js`, tests on the JSON plus one browser test), within its 15 notes.

**The dashboard reads the database only, apart from F5's request route.**

### Done when
- for a fixture with a developer ticket working on Qwen and two merged today: the developers' Qwen machine is `working` with that crate; `queue→developers` counts 1 and `checks→merged` counts 2; `developers→checks` isn't carrying
- Sonnet, off `[roles] developer` and in `checkpoint`, is a reviewer machine; Copilot is a stand-in reviewer
- the seeds, planting, rows, ripe and stash counts equal the board's (`board.py`) for the same fixture
- a browser test opens `/` and finds one machine per agent and the queue's crates in run order
- `uv run runner check-all --task f3-01-factory-line` passes

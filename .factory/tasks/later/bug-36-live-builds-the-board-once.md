---
id: bug-36-live-builds-the-board-once
milestone: bugs
difficulty: 3
depends_on: []
area: factory
priority: 64
finding: f172-i-d-like-to-be-able-F3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/line.py
  - factory_dashboard/board.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
`/live`, polled every 5 s from every page, builds the board once per request.

### Context
Read `def _live_context` in `factory_dashboard/overview.py`, `def live_line` in `factory_dashboard/line.py` and `def reserve_marked` in `factory_dashboard/board.py`.
- Today the board is built twice per `/live`: inside `live_line` (its counts) and in `reserve_marked` (F172's cards past both marks), and each build reads every planted and growing card's doc from disk.
- Build it once in `_live_context` and hand it to both (an optional `board` argument on each, built as today when it's missing).

### Done when
- one `/live` request builds the board once (count the calls with `monkeypatch` on the builder)
- the page `/live` returns is the same as before for the same database
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

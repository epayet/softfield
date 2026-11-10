---
id: f228-02-one-floor-per-request
milestone: f228-loading-the-overview-page-is-slow
difficulty: 4
depends_on: []
files:
  - factory_dashboard/overview.py
  - factory_dashboard/line.py
  - factory_dashboard/board.py
  - factory_dashboard/planning.py
  - factory_dashboard/app.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
One Overview load, and one 5-second refresh (`/live`), builds the floor once and the board once, and shows exactly what it shows today.

### Context
Read `.softfield/cards/f228-loading-the-overview-page-is-slow.md` ("What happens today", D3, D4).
- Today the floor (`live_line` in `factory_dashboard/line.py`) is built by `overview` and `_live_context` in `factory_dashboard/overview.py`, and by `_ripe` in `factory_dashboard/planning.py`, which `desk` calls. `desk` itself runs twice: from `_live_context`, and from `top_bar` in `factory_dashboard/app.py`.
- The board (`board` in `factory_dashboard/board.py`) is built inside each `live_line`, and again by `reserve_marked`.
- Hand them down through optional arguments, each built as today when missing: `live_line(..., cards=)`, `reserve_marked(..., found=)`, `desk(..., line=)`, `_ripe(..., line=)`, `_live_context(..., line=)`.
- `overview` builds the line and passes it to `_live_context`. `_live_context` builds the board first and passes it to `reserve_marked` and `live_line`, and passes the line to `desk`.
- `render` in `factory_dashboard/app.py` calls `top_bar`, whose `planning_count` is then overwritten by the page's own context. When the context already holds `planning_count`, `top_bar` skips `desk`. Pages that give no count, like `/runs`, still get it from `top_bar`.
- Keep nothing between requests: no module-level cache and no `lru_cache`. A value lives only as long as its request.
- Add nothing to what `live_line` returns: `/line/live` sends it to the browser as JSON.
- Other cards also change these functions, so find them by name, not by line number.

### Done when
- one `GET /` and one `GET /live` each build the board once: count calls to `_cards` in `factory_dashboard/board.py` with `monkeypatch`
- one `GET /` and one `GET /live` each build the floor once: count calls to `trips` in `factory_dashboard/line.py` with `monkeypatch`
- `GET /runs` still shows the Planning tab's count, the same as `GET /`
- a card that turns ripe still shows on the desk, and in Needs you, on the next `/live`
- `/` and `/live` show the same page as before for the same database and clock: the existing tests in `tests/factory_dashboard/test_overview.py` pass unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 3800695
logs: .softfield/var/runs/20261106-011143/f228-02-one-floor-per-request
```

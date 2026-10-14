---
id: f1-01-metrics-db
milestone: f1
depends_on: []
agent: lead
difficulty: 6
files:
  - runner/metrics.py
  - runner/config.py
  - workflow/runner.toml
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_config.py
---

### Goal
`runner/metrics.py` holds the factory's metrics database: D2's tables, their migrations, and the functions that open it and write each kind of row.

### Context
Read `docs/milestones/f1.md` (D1, D2, D6) and `docs/adr/13-factory-dashboard.md` §1. Test-first, in `tests/runner/test_metrics.py`.
- `open_db(path)` creates the folder and the file, turns on WAL and foreign keys, and migrates by `PRAGMA user_version` (a list of migration steps; version 1 is D2's schema). A second open is a no-op.
- One write function per fact, each an upsert on D2's natural key, so the runner (f1-02, f1-03) and the backfill (f1-04) can call them twice safely. Times are parameters, never read from the clock inside; the module does no other IO.
- Keep it one module of plain functions over a `sqlite3.Connection`, with no ORM. f1-02 to f1-04 decide which functions they call; name them after the table (`upsert_ticket`, `start_job`, `finish_job`, `update_running_job`, `add_finding`, …).
- `[metrics] db` in `workflow/runner.toml` (default `~/.local/share/software-factory/factory-metrics.sqlite`, `~` expanded) becomes `Config.metrics_db` in `runner/config.py`.
- **Tests never touch the real path:** they use `tmp_path`.

### Done when
- a fresh path gets every D2 table and `user_version` 1; opening it again changes nothing
- writing the same run, ticket, job (run, ticket, role, attempt) or finding twice leaves one row, with the later values
- `finish_job` sets the end, the outcome, tokens, gates JSON and the rest; `update_running_job` changes only the live fields
- a ticket row keeps `difficulty` and `difficulty_corrected` apart
- `load_config` reads `[metrics] db` and falls back to the default when it's missing
- `uv run runner check-all --task f1-01-metrics-db` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```

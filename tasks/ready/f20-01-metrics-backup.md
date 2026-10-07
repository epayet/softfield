---
id: f20-01-metrics-backup
milestone: f20-data-safety
difficulty: 5
depends_on: []
agent: lead
files:
  - runner/backup.py
  - runner/config.py
  - runner/loop.py
  - workflow/runner.toml
tests:
  - tests/runner/test_backup.py
---

### Goal
The runner copies the metrics database into a Dropbox folder once a day, keeping the last 14 copies, without ever stopping the run when a copy fails.

### Context
Read `docs/milestones/f20-data-safety.md` (D1 is the decision: config, file names, when it is due, failures, pruning), `runner/config.py` (`load_config`, how `[metrics] db` is read), `runner/metrics.py` (`open_db`), and in `runner/loop.py` `run_session`, `wait_for_claude` and `_hold_for_the_owner`.
- The live database runs in WAL mode with the dashboard reading it: copy with `sqlite3.Connection.backup`, never a file copy.
- Check at the run's start, at each pick, and in each wait, including the wait when nothing is ready. A check costs one `stat` of `dir` when no copy is due.
- A failure is a session-report note and a console line; the next check tries again.
- **Never put the live database, its `-wal` or `-shm` in `dir`; only finished copies, renamed into place.**

### Done when
- with no copy in `dir`, a run's start writes `factory-metrics-<YYYYMMDD-HHMM>.sqlite`, and it opens with the same tables and rows as the source
- a copy newer than `every_hours` means no new copy; once older, the next pick or wait writes one
- with `keep = 2` and three copies, the oldest is removed and a file in `dir` not matching the pattern is left alone
- `dir` missing is created; `dir` not writable gives one report note and the run goes on to its ticket
- a long wait (fake clock past `every_hours`) writes a copy without a pick
- `workflow/runner.toml` has the `[backup]` section with D1's defaults, and a config without it uses those defaults
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

---
id: f187-03-old-times-to-utc
milestone: f187-store-every-time-in-utc-the
difficulty: 4
agent: lead
depends_on: [f187-01-runner-clocks-utc, f187-02-pages-show-local-time]
files:
  - runner/metrics.py
  - runner/loop.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_loop.py
---

### Goal
The metrics database's old times are converted to UTC once, right after a backup copy holds them as they were.

### Context
Read `.factory/cards/f187-store-every-time-in-utc-the.md` D5 (the columns and the rules). In `runner/metrics.py`: `ONCE_STEPS`, `once`, `open_db` (a new database marks its steps done). In `runner/loop.py`: `check_backup`. In `runner/backup.py`: `copy`. Follow F55's once step (`CLEAR_OUT` in `runner/requests.py`).
- Add `"f187 utc"` to `ONCE_STEPS` and a function in `runner/metrics.py` that converts D5's columns in one transaction and returns how many values it changed.
- `check_backup` runs it when the step isn't done, right after a copy is written; with no backup set (`s.backups` None), it first writes a copy with `backup.copy` into the database's own folder. Mark the step done only when the conversion commits.
- A unique key collision rolls the whole conversion back: nothing changes, nothing is deleted, the step stays owed, and the console and the run's report say so once.
- **Protected work: test-first.** The owner's data: the test checks the copy made before still holds the old values.

### Done when
- a database with `+01:00` and `+00:00` rows in each D5 column has only `+00:00` values after the step, each the same instant as before
- NULLs, `new` in `once_steps` and a plain date are left as they are
- the copy written just before still has the `+01:00` values
- the step runs once: a second backup copy converts nothing and logs nothing
- with no backup set, a copy appears beside the database before the conversion
- a collision on `usage_events`' key leaves the database unchanged and the step owed, with one console line
- the console says "converted N stored times to UTC (F187)"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

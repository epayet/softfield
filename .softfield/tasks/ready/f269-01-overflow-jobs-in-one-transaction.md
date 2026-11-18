---
id: f269-01-overflow-jobs-in-one-transaction
milestone: f269-tests-factory-dashboard-test-jobs-py
agent: developer
difficulty: 1
tests_only: true
depends_on: []
files:
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_jobs.py
---

### Goal
`write_more_jobs` writes its jobs in one transaction, so the setup of `test_more_than_200_jobs_shows_200_and_count` takes under a second instead of about 13 s.

### Context
Read `write_more_jobs` in `tests/factory_dashboard/conftest.py` and `open_db` in `runner/metrics.py`: the connection is in autocommit (`isolation_level=None`, WAL), so each of the loop's 615 writes (`upsert_ticket`, `start_job`, `finish_job`, 205 times) is its own transaction with its own sync to disk. None of those three functions commits or opens a transaction itself. Follow `set_board_order` in `runner/metrics.py`: `conn.execute("BEGIN IMMEDIATE")`, the writes, `conn.execute("COMMIT")`, and `ROLLBACK` then re-raise on any exception. Found in F71's review (F3, `.softfield/reviews/f71-i-suspect-we-might-need-to.md`).

### Done when
- `write_more_jobs` wraps its loop in one `BEGIN IMMEDIATE` … `COMMIT`, rolling back and re-raising on an exception, as `set_board_order` does
- its signature, its docstring's meaning and the rows it writes are unchanged; `runner/metrics.py` is not touched
- `test_more_than_200_jobs_shows_200_and_count` passes unchanged, and `pytest tests/factory_dashboard/test_jobs.py --durations=5` shows its setup under 1 s (quote the before and after times in the commit message)
- no other fixture or test is changed
- all gates pass (see `docs/workflow.md`)

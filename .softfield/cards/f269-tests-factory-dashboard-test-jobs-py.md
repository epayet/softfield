# Milestone F269: The 200-jobs test writes its jobs in one transaction

> **State:** done · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-20. Base: git tag `f269-tests-factory-dashboard-test-jobs-py-start`. Report: [`.softfield/reviews/f269-tests-factory-dashboard-test-jobs-py.md`](../reviews/f269-tests-factory-dashboard-test-jobs-py.md).
> Planted by the owner on 2026-11-18.

## Notes
tests/factory_dashboard/test_jobs.py's test_more_than_200_jobs_shows_200_and_count spends 13 s in setup writing 200 jobs one at a time: write them in one transaction so it takes under a second. From F71's review.

## Plan
One developer ticket, `f269-01-overflow-jobs-in-one-transaction`: `write_more_jobs` in `tests/factory_dashboard/conftest.py` wraps its loop in `BEGIN IMMEDIATE` … `COMMIT`, as `set_board_order` in `runner/metrics.py` does. The test files only; the runner and the dashboard are untouched, so no mock-up.

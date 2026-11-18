# Milestone F269: tests/factory_dashboard/test_jobs.py's…

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
tests/factory_dashboard/test_jobs.py's test_more_than_200_jobs_shows_200_and_count spends 13 s in setup writing 200 jobs one at a time: write them in one transaction so it takes under a second. From F71's review.

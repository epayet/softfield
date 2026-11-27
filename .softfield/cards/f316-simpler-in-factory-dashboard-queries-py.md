# Milestone F316: Simpler: in `factory_dashboard/queries.py`, `away()` walks…

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-27.

## Notes
Simpler: in `factory_dashboard/queries.py`, `away()` walks its jobs four times (last job, attempts, first start, and each merged ticket's developer outcomes rescanned per row); one pass building a record per ticket would save about 20 lines and the per-row rescan. From F132's review.

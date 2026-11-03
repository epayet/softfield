# Milestone F200: Where the hours went, in softfield report, for reviews to quote

> **State:** idea · **Priority:** 100 · **Area:** factory
> From docs/backlog.md (f53-review), written by the lead on 2026-11-02.

## Notes
Each review works out "What clogged the factory line" for itself: since ADR 28 it can read the metrics database with `softfield look sql`, but it writes its own queries each time, and they can disagree with the dashboard's. Give `softfield report` a "where the hours went" block (limit waits, failed attempts, stops for the owner, from what `factory_dashboard/queries.py` already computes for the floor) for reviews to quote.

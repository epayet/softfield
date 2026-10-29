# Milestone F187: Store every time in UTC, show local time on screen only

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-29.

## Notes
Store every time in UTC. The runner writes local time (+01:00 before 25 Oct) and the dashboard writes UTC, so times sort wrong as text. Write UTC everywhere, show local time on screen only, and convert the old rows once after the daily backup.

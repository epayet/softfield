# Milestone F34: planner tasks cannot be paused but overview now still says 'paused by you' even if it's currently running under pause

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
- **The owner (2026-10-08):** planner jobs run during a pause (f6-14), yet the overview's Now panel still says only "Paused by you since HH:MM" while one runs.
- **The cause (lead, from the code):** the top bar already says "Paused by you since HH:MM · the lead is answering you" (f6-23, `factory_status` in `factory_dashboard/app.py`), but Now's pause line (`_partials/running.html`) builds its own words from `paused_clock` and `pausing` in `overview.py`. Same root as F29: Now ignores a resume on its way too, so it keeps a Resume button while the bar says "Resuming…".
- **The fix:** one ticket (developer, follows f6-23's tests): Now's pause line shows the bar's own status (`bar_status`: words, tone and button), so the two can't disagree again; drop `paused_clock` and `pausing` from the overview context if nothing else reads them. Tests: paused with a live planner job → Now reads "· the lead is answering you"; resume asked → "Resuming…" and no Resume button; plain pause unchanged.

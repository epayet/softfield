# Milestone F33: overview now check-all how long

> **Status: planned** (2026-10-08, with the owner, in the planning room). **State:** ready · **Priority:** 19 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
does'nnt say for how long it's been running, but it does with other tasks. it'd be good to have an estimate of how long the currente now task is estimated to be finished, i believe we do that in other places

## Outcome
- Whatever Now shows, a job or the runner's own work between jobs (check-all, the gates, the warm-up), says how long it has been running, and roughly how long it has left.
- The estimate is the one the planning room already gives for "the next reply" (`_typical` in `factory_dashboard/planning.py`): the average of the last finished ones of the same kind. The two pages never disagree.

## Why check-all has no time
- A job is a row in `jobs` with its `started`, so Now shows "Elapsed". Check-all, the gates and the warm-up aren't jobs: the runner only writes its words to `runs.activity` (`set_activity` in `runner/loop.py`), with no start time, and keeps no record of how long each took. So there is nothing to show, and nothing to estimate from.

## Decisions
- **D1 The runner records its own work's clock** (lead, `runner/` is protected): when the activity is set, the run stores since when (`runs.activity_since`); when a `doing` block ends, one row in a new `activity_spans` table (run, kind, started, ended). The kind is the activity's first words before " · " (`check-all`, `gates`, `warm-up`), so `check-all · f6-06` and `check-all on main` count as `check-all`. Restoring the activity before it restores its `since` too.
- **D2 Now shows both lines** (developer): "Running for 3 min" and "About 4 min left", or "Any minute now" once it is within a minute, or "Longer than usual (about 6 min)" once past it. No estimate line without history. The same for a job's card, from `_typical` moved next to `running_jobs` so both pages share it.
- **D3 The estimate stays rough on purpose:** average of the last 10, by kind (and for jobs, by role and agent, as today). Not by difficulty yet: if the job estimates turn out poor, that's one change in the shared helper.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | activity-clock | L | 4 | – | D1: `runs.activity_since`, the `activity_spans` table, and `typical_activity(kind)` |
| 02 | now-estimate | D | 3 | 01 | D2: Now's "Running for" and "left" lines, for jobs and the runner's own work |

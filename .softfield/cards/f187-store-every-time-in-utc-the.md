# Milestone F187: Store every time in UTC, show local time on screen only

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-29.

## Notes
Store every time in UTC. The runner writes local time (+01:00 before 25 Oct) and the dashboard writes UTC, so times sort wrong as text. Write UTC everywhere, show local time on screen only, and convert the old rows once after the daily backup.

## What we know (2026-10-29)
- The machine's clock is on UK time: `+01:00` until 25 Oct, `+00:00` since, and `+01:00` again from 28 Mar 2027.
- The runner's clocks are local: `runner/loop.py` `now()` (`datetime.now().astimezone()`), `runner/owner.py` `_now`, `runner/cli.py` (the first card's thread), and `runner/backfill.py`'s `_iso_ms`, `_iso_mtime` and run start. The dashboard's clock is UTC (`factory_dashboard/app.py` `get_now`), so the owner's requests mix both: before 25 Oct, 666 rows written by the dashboard at `+00:00` and 154 by the runner at `+01:00`.
- Rows at `+01:00` today: jobs 1,377, usage events 1,514, runs 458, planner messages 516, desk items 192, requests 154. Every value carries its offset: none is naive, so each converts exactly, the repeated hour of 25 Oct included.
- About 30 queries compare or order times as text (`ORDER BY created`, `at > ?`, `MAX(ended)`) in `runner/` and `factory_dashboard/`; F86 (Tracking the time the owner spent) already had to work around it.
- Some screens print a stored time as it is (`factory_dashboard/app.py` `_clock`, `overview.py` line 82, `board.py`'s "since 29 Oct"), others convert first (`line.py`, `coming.py`, `_partials/away.html`). With UTC stored, the first kind would show UTC in summer.

## Outcome
Every time the factory stores is UTC (`…+00:00`), so ordering as text is ordering in time, in summer too. Every screen, console line and report shows local time, as today. The old rows are converted once, right after a backup copy, and nothing shown changes.

## Done when
- after the next run starts and its backup copy is written, `softfield look sql "SELECT count(*) FROM jobs WHERE started NOT LIKE '%+00:00'"` gives 0, and the same for requests, messages, desk items, usage events and runs
- the console says once "converted N stored times to UTC (F187)"; the Dropbox copy taken just before still has the `+01:00` rows
- the Overview, the line, the desk and a thread show the same clock times as before the change
- with the machine's zone set to Paris in the tests, a time stored as `08:00+00:00` shows as 09:00 on every page and console line that the tests cover

## Decisions
- **D1. One format.** A stored time is `moment.astimezone(UTC).isoformat()`: `2026-10-29T08:14:44.098011+00:00`, the format the dashboard writes today, so every reader (`datetime.fromisoformat`) keeps working. Not `Z`, not epoch numbers.
- **D2. Fix the clocks, not the 60 writers.** The runner's four clocks above return UTC; the call sites that write `now.isoformat()` stay as they are. `runner/metrics.py`'s docstring says it: times are stored in UTC, shown in local time.
- **D3. Local only where a person reads it.** Anything formatted for the owner (a page, the console, a report, a desk item's words, a planner's view of a thread) goes through `.astimezone()` first. On the dashboard, one helper, `local(at: str | datetime | None) -> datetime | None` in `factory_dashboard/queries.py`, used by every page that prints a clock time; the private `_clock`/`_when` copies call it. Pages that already convert keep doing it.
- **D4. Names and dates stay local.** Run folder names (`20261029-081443`), backup file names, and dates written into card docs and tickets ("Planted by the owner on 2026-10-29") stay in local time: they are names the owner reads, and `runner/backfill.py` reads old run folders as local.
- **D5. The conversion, once.** A once step `f187 utc` (`metrics.ONCE_STEPS`, F55 D3; a new database starts with it done). It runs in `runner/loop.py` `check_backup`, right after a copy is written, so that copy holds the old rows; on a machine with no backup set, it first writes one with `backup.copy` beside the database. One transaction over these columns: milestones `started`, `ended`; runs `started`, `ended`, `heartbeat`, `waiting_until`; jobs `started`, `ended`; rating_changes `at`; usage_events `at`, `resets_at`; owner_items `created`, `resolved`; owner_requests `created`, `done`, `dismissed`; work_queue `created`, `not_before`, `done`; planner_threads `created`, `archived`; planner_messages `at`; once_steps `at`; projects `paused`. A value converts only when `datetime.fromisoformat` reads it with an offset; anything else (NULL, `new`, a plain date) stays as it is. If a converted value collides with a unique key, the whole step rolls back, is not marked done, and says so once on the console and in the run's report; nothing is deleted.
- **D6. Tests in another zone.** The tests of 01 and 02 set the zone to `Europe/Paris` (`TZ` and `time.tzset()`), so local is not UTC and a slip shows; today UK winter time equals UTC and would hide one.
- **D7. Who builds.** 01 and 03 lead (`runner/` is protected, and 03 rewrites the owner's data: test-first); 02 developer (one helper and its uses, following `line.py`'s `_when`).
- **D8. Order.** 03 waits for 01 and 02: once old rows are converted, no clock may still write local time, and every screen must convert.

## Later
- the product (`coucou/`): Django's own `USE_TZ`, not part of this card
- the runner's JSON state (`.softfield/var/runs/state.json`: the pause and the 24-hour switches) is written in UTC from 01 on; its old values lapse within a day, so nothing converts them

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | runner-clocks-utc | lead | 4 | | D1–D4, D6 |
| 02 | pages-show-local-time | developer | 3 | | D3, D6 |
| 03 | old-times-to-utc | lead | 4 | 01, 02 | D5 |

# Milestone F234: The bar says "picking the next ticket" only while the runner is really picking

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-06.

## Notes
If it says running picking the next ticket, but is actually not doing anything, it's not picking up tickets it should be clearer and the dot should not be green

## Outcome
- The top bar says "Running: … picking the next ticket" with the green dot only while a run really is between two steps (a few seconds). A project that is only waiting for its turn, or has nothing it can run, says why it waits, with the grey dot.
- If a run ever sits on "picking the next ticket" for more than 5 minutes (the runner hung), the bar says "No progress since 16:02 · picking the next ticket" with a steady red dot and red words, never a green one (the owner, 2026-11-09: hazard yellow was too close to the lead's orange).

Mock-up: [`f234-mockup/stuck-picking.html`](f234-mockup/stuck-picking.html).

## Why it says so today
Read on 2026-11-09 from the metrics database: travel-companion's run (run 688) and coucou's (run 690) have said "picking the next ticket" since 2026-11-05 16:56, with fresh heartbeats, while neither ran anything.
- `work_queue` in `runner/loop.py` writes `PICKING` at the start of every turn. With several projects (`run_projects`, ADR 30 item 6) each round first gives every project a turn for its queued jobs only (`take_tickets=False`); such a turn that runs nothing returns without writing anything else, so the run keeps "picking the next ticket". Only the ticket turn writes the idle line, and a project gets none when an earlier project ran something that round.
- `factory_wide_status` in `factory_dashboard/app.py` ranks a "Running: …" line above "Idle: …" (F132 D1), and `factory_status` gives it the green `runner` dot (F184 D1). So whenever softfield is between jobs or idle, the bar shows "Running: travel-companion · picking the next ticket", green, with nothing happening.
- Separately, the heartbeat is a thread of its own (f1-49): a runner whose main loop hangs keeps a fresh heartbeat, and its last words stay forever.

## Decisions
- **D1 A turn never ends on "picking the next ticket"** (lead, `runner/`): when `work_queue` returns without running anything under `wait=False`, the run's activity is the idle line (`_idle_line`), whatever `take_tickets` was. When it held tickets back only because the turn took no tickets, the line says they wait their turn ("Idle: 2 tickets wait for their turn"), not "nothing can run". `PICKING` stays the words of the seconds in between.
- **D2 The run records since when** (lead, `runner/metrics.py`): `runs` gains `activity_since` (a migration, UTC ISO time), written by `update_run_activity` whenever the activity's text changes, cleared with it. Nothing else reads it yet.
- **D3 A stale pick is said, in red** (developer, `factory_dashboard/`): in `factory_status`, a live run whose activity is `PICKING` and whose `activity_since` is more than 5 minutes old returns "No progress since HH:MM · picking the next ticket", tone `fail`, dot `stuck`: a steady `--fail` dot, no halo, no breathing, and the words in `--critical-ink` (the existing `.words.fail`). Red, not hazard yellow: yellow sits beside the lead's orange dot and the waiting ring, and no other dot is red (the owner, 2026-11-09). `factory_wide_status` ranks it with Idle (after any "Running: …"). Only `PICKING` is checked: check-all and the gates can rightly take many minutes, and they have their own words.
- **D4 What doesn't change:** the green dot's meaning (F184), the order of the other statuses (F132 D1), the heartbeat.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | turn-says-why-it-waits | L | 3 | – | D1, D2 |
| 02 | stuck-picking-in-red | D | 2 | 01 | D3 |

## Before and after
- `/`
- `/planning`

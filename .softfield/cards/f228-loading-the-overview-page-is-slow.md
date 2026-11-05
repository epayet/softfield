# Milestone F228: The Overview and Milestones pages draw in about a second, softfield's too

> **State:** ready · **Priority:** 3 · **Area:** factory
> Planted by the owner on 2026-11-05.

## Notes
Loading the overview page is slow, especially for softfield

## What happens today (measured 2026-11-05, on the live database)
Each figure is one `softfield look page` from start to finish, so about 0.8 s of it is the command starting up; that start-up doesn't happen on the live server. The softfield Overview was read twice, the others once, with one planner job running. Where the time goes inside a page is read from the code and fits the figures; no profiler has run.

| Page | Time | Beyond start-up |
|---|---|---|
| Overview, coucou | 0.8 s | – |
| Runs, softfield | 1.0 s | 0.2 s |
| Board, softfield | 1.0 s | 0.2 s |
| While you were away alone (`/away`), softfield | 1.0 s | 0.2 s |
| The 5-second refresh (`/live`), softfield | 1.9 s | 1.1 s |
| **Overview, softfield** | **6.6 s** | **5.8 s** |
| **Milestones, softfield** | **24 s** | **23 s** |

- **The Claude per milestone chart is most of it, about 4.6 s.** Milestones draws the same data, `queries.trends`, five times, and five times 4.6 s is its 23 s. `spend_chart` in `factory_dashboard/overview.py` calls it once.
- **Why it grows with softfield:** `trends` calls `savings` for each of the 241 milestones, and each call runs `_lead_rates` again, which reads the jobs table once per merged lead ticket. Nothing in the table is indexed by ticket or milestone, so each read scans all 1,841 jobs. Coucou has 6 milestones.
- **The rest, about 1 s, is the floor built several times.** One Overview builds `live_line` four times and the board five: `overview`, `_live_context`, `_ripe` under `desk`, and `_ripe` again under `top_bar`, whose count `render` then throws away because `_live_context` already gave one; `reserve_marked` builds one more board. The 5-second refresh builds three floors and four boards, for as long as the page is open.

## Outcome
Softfield's Overview draws about as fast as coucou's, however many cards it grows to, and nothing on the page changes.

## Done when
- f228-01 to f228-03 merged.
- To test: open the Overview on softfield, then Milestones. Each appears in about a second, with the same numbers as before.
- The card's "Measured after" section gives the same table's figures again, on the live database.

## Decisions
- **D1: `trends` works out the lead's rates once** and hands them to each milestone (`_milestone_savings` already takes them). `_lead_rates` becomes one query, not one per ticket. The numbers don't change.
- **D2: Milestones calls `trends` once** and draws its table and four charts from that one answer.
- **D3: one floor and one board per request.** Each is built once and handed down through optional arguments, built as today when missing: `live_line(..., cards=)`, `reserve_marked(..., found=)`, `desk(..., line=)`, `_ripe(..., line=)`, `_live_context(..., line=)`. No cache and nothing kept between requests, so nothing can go stale.
- **D4: `render` skips the top bar's desk count when the page already gave one** (`planning_count` in its context).
- **D5: three indexes**, a new migration: `jobs (ticket_id)`, `jobs (milestone_id)` and `tickets (milestone_id)`. They only speed up reads, and change no data.
- **Tests count, they don't time:** a test on a time limit fails on a busy machine, so the tests count SQL statements and builds, and f228-03 measures the real times once.
- **The chart stays until F132 removes it:** f132-04 (F132, One view of the whole factory) already takes `#spend` and `spend_chart` off the Overview. This card makes the chart cheap, so that ticket stands as written.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | trends-reads-once | D | 3 | – | D1, D2 |
| 02 | one-floor-per-request | D | 4 | – | D3, D4 |
| 03 | indexes-and-measure | L | 2 | 01, 02 | D5, the figures again, bug-36 removed |

No mock-up: nothing on screen changes.

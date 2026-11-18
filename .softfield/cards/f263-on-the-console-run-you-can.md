# Milestone F263: Show the lead's direction to a developer's last attempt on the Overview

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-17.

## Notes
On the console run you can see the advice the lead gave a ticket when it got directed, I'd like to see that on the dashboard too in overview

## Expected outcome
The Overview shows the lead's direction (the advice Opus writes before a developer's last attempt) wherever that attempt shows: in Now while it runs, its first line on a plate under the ticket's title with the whole text a tap away, and folded in its row in While you were away once the ticket has merged. Picture: `.softfield/cards/f263-mockup/direction-on-overview.html`.

**Done when:** during a directed last attempt the Now panel shows the direction's first line (two lines at most on a phone) and opens to the whole of it; a merged ticket that had a direction keeps it folded in its away row; a ticket with no direction looks as it does today.

## Decisions
- **D1. The direction is kept in the database, not read from the run folder** (f263-01). Today its text lives only in `direction.md` in the ticket's logs folder, which can sit in an earlier run's folder (a parked direction) and is overwritten by the next one. A new column `jobs.direction TEXT` (migration `_V17` in `runner/metrics.py`, beside `_V16`) holds it on the direction job's own row; `metrics.set_job_direction(conn, job_id, text)` writes it, following `set_job_model`. `loop.give_direction` calls it once `direction.md` is read, with the whole text as written (the ticket repair, `ticket.md`, is not stored). Nothing is backfilled: only directions given after f263-01 show.
- **D2. Which direction a job shows:** for a `last-attempt` job, the newest `direction` job of the same `ticket_id` that started before it and has a `direction`. For an away row, the newest such job of the ticket. One query each, in the dashboard; no other page changes.
- **D3. How it is drawn:** a `details.direction` plate (styles in `factory_dashboard/static/dashboard.css`, new rules only, no new token): the plate, the notch and a 3 px Opus edge (the author's colour, not a status). Its summary is "The lead's direction" with "Opus · HH:MM" (Now) or "Opus · before attempt N" (away) and, in Now only, the first line (`runner.console.first_line`) clamped to two lines. Opened, the whole text renders through `factory_dashboard.milestones._to_html` (escaped), with a link to the direction's job page and its cost. Closed by default. The Now panel is redrawn every 5 s, which would snap an open plate shut: an open `details.direction` holds the refresh as a half-typed comment does (`window.liveIdle` in `factory_dashboard/templates/base.html` returns false while one is open), and folding it lets the page catch up.

## Before and after
- `/`

## Tickets
- f263-01-direction-kept-in-the-database (lead): D1
- f263-02-direction-in-now (developer): D2, D3 for the Now panel
- f263-03-direction-in-away-rows (developer): D2, D3 for While you were away

# Milestone F124: Pause one project from the Projects page

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

The database already has a pause per project (`projects.paused`, metrics V13) and the runner
skips a paused project (`cli._project_configs`); `softfield init` uses it while a project is
set up ("setting up", released by `softfield doctor`). Nothing on the dashboard sets it.

Give each project a Pause / Resume on the Projects page, as a request shown as on its way until
the runner takes it (owner.md, 2026-10-07). For when one project should wait while another runs,
without pausing the whole factory. Today "Pause after this job" on a project's Overview pauses
every project's tickets (a pause in any project holds every ticket, ADR 30 session D).

## What happens today (from the code and the database, 2026-10-27)
- `projects.paused` holds "setting up", "forgotten" or NULL; all three projects are NULL. ADR 30 item 6 already gives projects "a `paused` switch"; the global pause stays the machine's.
- A project with any `paused` is dropped from `_project_configs` (`runner/cli.py`), so `run_projects` (`runner/loop.py`) closes its session: nothing of it runs, **its requests are never taken** (they are read per project, at its own pick, `apply_requests` in `runner/requests.py`), and its planning room stops answering. A Resume sent from the dashboard to such a project would wait for ever.
- The top bar's Pause is a `pause` request on one project's row; it sets that project's `state.owner_pause`, and `project_round` holds every project's tickets while any one has it. Planning replies still go (`dispatch.pick(..., paused=True)`).
- The Projects page says "Paused: the runner leaves it alone." for any non-null `paused` other than "setting up", but nothing sets one.

## Outcome
Each project on the Projects page has its own Pause and Resume. A project paused by the owner finishes the job it is on, then runs none of its tickets, checkpoints or reviews, while its planning room keeps answering and its approvals go through; the other projects carry on. The top bar's Pause still holds the whole factory.

## Done when
- f124-01 and f124-02 merged (f124-03, the stretch, once F132's Next in line has landed).
- To test: on the Projects page press Pause on coucou. The button turns dashed orange, "Pausing…", at once; at the runner's next pick the row shows "Paused by you since HH:MM" with a hazard edge and a Resume. softfield's tickets keep running. Write a message on one of coucou's cards: the lead answers it. Press Resume: coucou's tickets are picked again.
- `softfield run --dry-run` says coucou's tickets are "paused by you", and a bare `softfield` lists coucou as "paused by you since HH:MM".

## Decisions
- **D1. What a project's pause holds.** The project's tickets, checkpoints, escalations and reviews: what the factory's pause holds (`dispatch.pick(..., paused=True)`), for that project alone. Its planning replies and its requests still go, so the owner can plan it and resume it. The job running when it takes finishes ("after this job", as the bar's). The factory's pause and a project's add up: either one holds that project's tickets.
- **D2. Where it is kept.** `projects.paused` holds the ISO time it took (the V13 comment: "when, once paused"); "setting up" and "forgotten" keep their meaning. `metrics.paused_by_you(row) -> str | None` gives the time for a time and None otherwise; nothing else parses the column. `_project_configs` skips "setting up" only (forgotten is out of `projects_in_order` already), so a paused project keeps its session and its requests are taken.
- **D3. Two request kinds**, `pause_project` and `resume_project`: no subject, no value, on the project's own row (the form's `project`), so `apply_requests` takes them at that project's pick, during the factory's pause too. They change only the database, never git: no clean main needed, like `project_order`. Results: "paused by you: its tickets wait after the job it is on", "already paused, since HH:MM", "resumed", "not paused", and "being set up: `softfield doctor` hands it over" for a project still setting up (never turned into a pause).
- **D4. What the runner says.** While held, the project's activity is `Idle: paused by you since HH:MM` (the `IDLE` prefix, so the top bar ranks it with the idle projects and never says the whole factory is paused). `--dry-run` gives its tickets the wait "paused by you"; a bare `softfield` lists it "paused by you since HH:MM", not the raw time.
- **D5. The Projects page** (f124-02), as `.softfield/cards/f124-mockup/projects.html` Proposed: a Pause / Resume button on each project's head line; pressed, it turns dashed orange "Pausing…" or "Resuming…" with the line "On its way: the runner takes it at its next pick, after the job it is on", and can't be pressed again, until the runner finishes the request (read from the latest open `pause_project` / `resume_project` row, as `order_on_its_way` reads the order). A paused project shows a hazard left edge and "Paused by you since HH:MM. Its tickets wait; its planning still answers you." A project being set up keeps its line and has no button.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | a-project-pauses-alone | L | 5 | – | D1–D4: the kinds, the hold, the column, the console's words |
| 02 | pause-on-the-projects-page | D | 3 | 01 | D5 |
| 03 | next-in-line-says-paused | D | 2 | 01, f132-02 | stretch: F132's Next in line says "Paused by you" for a paused project instead of listing its tickets as next |

01 is the lead's: `runner/` and `factory_dashboard/requests.py` are protected, and it changes which projects keep a session. 02 follows the Projects page's own order form, a button that asks the runner (`.softfield/developer.md`).

The mock-up: `.softfield/cards/f124-mockup/projects.html` (Today and Proposed, the real projects and counts of 2026-10-27).

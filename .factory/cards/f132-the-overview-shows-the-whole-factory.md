# Milestone F132: One view of the whole factory: the top bar, the Overview, Jobs and the floor

> **State:** ready · **Priority:** 2 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
From the terminal session of 2026-10-14 (ADR 30, after the owner's second `softfield init`).

The owner, 2026-10-14: "when i change project it stops showing what it's currently doing, that's
not good. the project change is just for planning and board, not for the overview and general
things that talk about what the factory is doing."

Done already: the top bar's status covers every project (`app.factory_wide_status`): a pause
first, then a running job, a wait for Claude, anything live, Stopped last; it names the project
when there is more than one, and its Pause / Resume posts to that project.

Still per project, and should be the whole factory's:
- the Overview: Now (running jobs), Next in line (the queue), Needs you, Coming, While you were
  away, allowances, the line on the Overview (`factory_dashboard/overview.py`, `_live_context`,
  `/live`);
- the Line page (`/line`, `/line/live`), Jobs, Runs, Timeline: what the factory did, with each
  item naming its project.

Stays per project (the picker's job): Planning, Board, Tickets, Milestones, a project's page.

Open questions: does the picker stay in the top bar, or move into the per-project pages only? How
does the Overview show several projects' queues: one list in the runner's real order (what
`softfield run --dry-run` prints across projects), each item tagged with its project?

A mock-up first (owner.md, 2026-10-09): Today and Proposed of the Overview on real data, two
projects running.

### From F160: the top bar on what's running atm is a bit buggy depending… (merged by the lead on 2026-10-20)
the top bar on what's running atm is a bit buggy depending on what project i'm looking at, it should the same regardless of current project viewed. similalrly, the overview should be the same across all projects, as there is one factory and runner for all projects. right now a developer ticket is working on softfield but top bar says Running: travel-companion · picking the next ticket.

### From F92: Claude per milestone on overview is not super useful… (merged by the lead on 2026-10-27)
Claude per milestone on overview is not super useful especially on mobile. 
Savings from delegating so far on M4, why is this stuck on M4?

What was said on F92's thread:
The owner said that Claude per milestone on the Overview isn't very useful, especially on a phone, and asked why the savings panel was stuck on M4. Answered: the panel follows the newest card not done yet, and F132's D8 (ticket f132-04) moves both panels to the project's page. Still open: whether the Claude-per-milestone chart needs a phone-friendly form once it is on the project page.

## What happens today (from the code and the database, 2026-10-20)
- **Why the bar named travel-companion.** One runner serves every project, but each project keeps its own run row (ADR 30, "One pick per project"): at 14:08 runs 342 (travel-companion), 344 (coucou) and 346 (softfield) all beat, and the two idle ones say "picking the next ticket" for as long as they wait their turn. `factory_wide_status` (`factory_dashboard/app.py`) ranks any "Running: …" the same, a real job or that between-jobs line, and keeps the first project in the owner's order: travel-companion (order 1). travel-companion has 9 ready tickets, so it isn't "Idle: nothing to do"; all 9 wait for m1-06-replan, parked for Claude's 5-hour window. The f17 review saw this and parked it in `docs/backlog.md` as "only one runner runs today"; since ADR 30 three do, in one process.
- **The bar is already the same on every page**: `factory_wide_status` ignores the project picked. It was wrong everywhere, not per page.
- **Everything else on the Overview is the picked project's**: Now, the Queue and Next in line, Needs you, the floor, While you were away (`_live_context`, `overview` in `factory_dashboard/overview.py`). Picking travel-companion shows Now as "Running: picking the next ticket" while softfield's job runs, and softfield's view never shows travel-companion's 4 desk items or its 5 merges since 20:00.
- **Savings names a card merged away.** "The newest milestone not done" (`current_milestone`) is now the newest plant: at 14:08 it was F160, merged into this card that morning (its milestone row stays). The Timeline's default filter uses the same function.
- Jobs, Runs and Timeline list the picked project's only (`jobs.py`, `runs.py`, `timeline_data`). Agents, Bench and the allowance already read the whole machine.

## Outcome
One factory, one view: the top bar names the job that runs, whichever project it is in; the Overview, Jobs, Runs, Timeline and the floor show every project, each item with its project's plate; the project picker sits with the three pages it changes (Planning, Board, Tickets).

## Done when
- f132-01 to f132-08 merged.
- To test: while a softfield ticket runs, open the dashboard on travel-companion's Overview, then on coucou's. The bar says "Running: softfield · <ticket>" with the developer's blue dot on both, and both Overviews are the same page: Now shows the softfield job, Needs you lists each project's desk, Next in line lists softfield's next tickets and says why travel-companion's are passed over.
- Jobs and Timeline show the softfield job and the travel-companion jobs of the morning together, each with its project.

## Decisions
- **D1. The bar follows the job** (f132-01). In `factory_wide_status`'s rank, a status whose dot is `lead` or `developer` (a live job) comes before any other "Running: …". Order: a pause (or a pause or resume asked), a live job, a wait for Claude, a between-jobs line ("Running: picking the next ticket", any other activity), Idle, Stopped. Among equals, the owner's project order, as today. The backlog line from the f17 review goes.
- **D2. What is the factory's, what is a project's.** Factory-wide: the top bar, the Overview, the floor (`/line`), Jobs, Runs, Timeline, Agents, Bench, Projects. A project's: Planning, Board, Tickets, Milestones, a project's page and everything under them. A factory-wide page ignores `?project=` for what it shows; every link from one of its rows carries the row's own project (`?project=travel-companion`), so a tap opens the right project's page.
- **D3. The project plate** (f132-02): `factory_dashboard/templates/_partials/project_plate.html`, given `name`, draws `<span class="proj">name</span>`; `.proj` in `dashboard.css` is the mock-up's: mono, ink-2 on the plate, a rule border and two corner ticks, no status colour. It shows only when the factory has more than one project: `render` adds `many_projects` (more than one name in `projects`).
- **D4. Every project, one function.** `overview.every_project(conn, project) -> list[str]`: the names `metrics.projects_in_order` gives, forgotten ones left out, or `[project]` when it gives none. Every factory-wide view loops over it; nothing else decides which projects count.
- **D5. Next in line is the runner's order** (`project_round` in `runner/loop.py`): every project's queued jobs first (planning replies, reviews, directions), in the project order; then the tickets that can run, project by project in the order (a project's own order inside, as `live_line` gives it today); then the waiting ones. A project that goes first in the order but has no ticket that can run gets one line, "Passed over: <project> goes first in your order, but …", with its first ticket's wait. The count says each project's share: "63 tickets waiting: softfield 54 · travel-companion 9".
- **D6. Needs you, per project**: one desk line for each project with something on its desk ("4 things wait on its desk", its top three, "Open ›" to that project's `/planning`), and every project's notices, each with its plate. `data-notices` stays as f142-01 (F142, Phone notifications: every project) builds it.
- **D7. The picker moves into the tab strip** (f132-08), in front of Planning, Board and Tickets, the three as one bay; the bar's top row keeps the brand, the status and the theme. The tab order doesn't change. A factory-wide page's crumbs start "The whole factory" instead of a project's name.
- **D8. Savings leaves the Overview** for each project's page (`/projects/<name>`, `project.html`), as "Savings from delegating on <project>, so far" over all its milestones (`queries.savings` with no key), its three figures as today. `current_milestone` goes once nothing calls it.
  - **Claude per milestone goes** (owner, 2026-10-27, from F92: "not super useful, especially on mobile"): not moved, removed. The Milestones page already charts Claude's dollars per merged ticket and the net savings per milestone.
- **D9. The floor, every project** (f132-05): one floor, as the factory has one set of machines. The field counts every project's cards per stage, a crate's label starts with its project's plate when there are several, the stash counts every project's merges. `live_line` and `replay` take the list from `every_project`.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | bar-follows-the-job | D | 3 | – | D1 (priority 2: a wrong status on every page) |
| 02 | overview-live-every-project | L | 6 | f142-01 | D2–D6 for Now, the Queue, Next in line, Needs you |
| 03 | away-every-project | D | 3 | 02 | While you were away, every project, with plates |
| 04 | savings-on-project-page | D | 3 | 02 | D8: savings to the project's page, the chart removed (replan 2026-10-27) |
| 05 | floor-every-project | L | 6 | 02 | D9 |
| 06 | jobs-runs-every-project | D | 3 | 02 | Jobs and Runs list every project, a Project column |
| 07 | timeline-every-project | D | 3 | 02, 04 | the Timeline's lanes carry every project; the last 24 h by default |
| 08 | picker-in-the-tabs | D | 2 | 02 | D7 |

02 waits for f142-01, which reworks the same `_live_context` and notices first (it runs at priority 3). 02 and 05 are the lead's: each changes a large module several pages read, and 02 sets the plate and `every_project` the developers' tickets copy.

The mock-up: `.factory/cards/f132-mockup/overview.html` (Today and Proposed, real values of 2026-10-20 14:08).

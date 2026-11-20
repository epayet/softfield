# Milestone F279: The queue: the whole factory's line on one page, in the runner's order

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-19.

## Notes
I would like to be able to see the queue across the whole factory. in planning atm it's per per project, which makes sense. overview only shows the next few things, which is probably fine. is that worth a new page? want to see every ticket from which project, or things like checkpoints setup, etc. and it should be recomputed each begining of new task, ie out of tokens so just dev tickets go next etc, the dry run should probably help. there should be a sentence to explain current state, like over pace or fast lane or things like that. in fact it should be a cool factory view, maybe part of the new overview map we wanted to do or is that too much? new page sounds overkill but could see the whole queue with details for each ticket

## What happens today (from the code and the database, 2026-11-19 20:40)
- **The whole queue:** 145 ready tickets (softfield 141, travel-companion 3, coucou 1) and 2 queued jobs (softfield's checkpoint on F265, wardrobe-teller's setup), with the lead's planner job on F279 running. 77 tickets can go (2 the developers', 75 the lead's), 68 wait for another ticket; f132-02-overview-live-every-project alone holds 10.
- **Over pace:** Claude's week 82% used against today's pace of 42%, so developers go first and the lead fills the gap (ADR 50 item 2).
- **Where it shows:** the Overview's Next in line shows 3 rows of the picked project (`live_line`, `queue[:3]`); the board is cards, per project; Tickets is per project, latest work first; `softfield run --dry-run` prints each project's list one after another (`runner/cli.py`), not the factory's one order.
- **Two orders:** the dashboard rebuilds the order itself (`queries.run_order`), without Claude's windows; the runner picks with `loop.choose_ticket` and `dispatch.plan`. bug-42 (set aside) is one place they disagree; bug-21 (set aside) is the dry run disagreeing with the run about jobs held by Claude.
- **Over pace is decided per project:** `project_round` asks each project in turn for a ticket, and `choose_ticket` lets a lead ticket fill the gap when *that project* has nothing else. So once travel-companion's m8-08-trip-by-hand is done, its lead ticket m5-01-remove-memory-place-row goes before softfield's developer ticket f269-01-overflow-jobs-in-one-transaction, though ADR 50 item 2 says the lead goes "when nothing else can start".

## Outcome
A page, **The queue** (`/queue`), shows the whole factory's line in the order the runner will take it: every project, every job (checkpoints, setups, reviews, planning) and every ticket, each with its project, who does it and why it sits there. One sentence at the top says what drives the order now ("Over pace: developers first, the lead when nothing else can"). The runner works the list out at each pick and stores it, so the page, the Overview's Next in line and `softfield run --dry-run` say the same thing.

The picture to build: `.softfield/cards/f279-mockup/queue.html`.

## Done when
- f279-01 to f279-05 merged.
- To test: open the Overview on the phone and tap "The whole queue". The page's sentence says what the top bar's allowance says (over pace, a limit, your pause, the fast lane). The first rows are the same as the Overview's Next in line, and travel-companion's tickets sit among softfield's with their plate. Tap a ticket: its goal, why it's there, what it waits for and any pre-flight problem open under it. Approve a plan: the page says it is on its way until the next pick, then its tickets are in the list. Run `softfield run --dry-run` in a terminal: the same order.

## Decisions
- **D1. The runner works out the plan; nothing else does** (f279-01). At each pick, before its job starts, and on a round that runs nothing (at most once a minute), the runner works out the whole factory's plan and stores it in the metrics database, one row replaced each time (`queue_plan`: `at`, `picked`, `body` as JSON). The dashboard shows it and never orders tickets itself. `softfield run --dry-run` prints the same plan, one list for the factory.
- **D2. The plan's shape** (f279-01): `dispatch.FactoryPlan(at, picked, sentence, facts, lines)`, and each line a `dispatch.PlanLine(project, kind, subject, title, who, group, waits, reason, card, early_for, preflight)`: `who` is `lead`, `developer` or None for a job; `group` is `lane`, `jobs`, `go` or `waits`; `preflight` the ticket's pre-flight problems. `loop.factory_plan(configs, at)` builds it; `metrics.store_queue_plan` and `metrics.latest_queue_plan` write and read it.
- **D3. The factory's order is `project_round`'s:** every project's fast lane, then the queued jobs project by project in the owner's order, then the tickets that can go project by project, then those that wait. Same as F132 D5.
- **D4. The sentence** is the runner's words, from the same inputs as `choose_ticket` (ADR 50 item 7), the first that applies: paused by you; main fails its tests on <project>; Claude at its limit until <time> (developers only); over pace or past a mark (developers first, the lead when nothing else can); the fast lane goes first; else "Your board's order, the lead and developers alike". Then up to three facts: Claude's reading ("week 82% used, today's pace 42%"), the developers' runway ("2 developer tickets can go now, about 35 min"), and what goes next.
- **D5. Over pace is the factory's, not a project's** (f279-02): a lead ticket fills the gap only when no project has anything else that can start, as ADR 50 item 2 says. A fix to the runner keeping an Accepted ADR, so no new ADR.
- **D6. The page** (f279-03): `GET /queue`, `factory_dashboard/queue.py`, `factory_dashboard/templates/queue.html`; factory-wide as F132 D2 says, so not a tab: the Overview's Queue panel and the map link to it. It says when the plan was worked out ("at 20:40, the runner's last pick"), and the owner's requests not yet applied that change the order (`owner_requests` with no `done`: approve_plan, reorder, project_order, queue, set_aside, pause, resume, reserve) as on their way, a dashed orange edge, "applied at the next pick". Rows fold open for their details. It refreshes every 30 s through `liveIdle`, like the other live parts.
- **D7. One source for Next in line** (f279-04): the Overview's Next in line and its count come from the stored plan's first rows, with a link "The whole queue ›". bug-42 then has nothing left to fix.
- **D8. The map links, it doesn't list** (f279-05): F199's map stays a picture with few words (F199 D5); its queue station opens `/queue`.
- **D9. Not in this card:** a start time per row (17 min a ticket times the place lies once the lead fills a gap); the planner's "where the work stands" reading the stored plan.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | the-runners-plan | L | 6 | – | D1–D4: the plan, stored at each pick, printed by the dry run; takes in bug-21 |
| 02 | gap-fill-across-projects | L | 4 | 01 | D5 |
| 03 | the-queue-page | D | 5 | 01 | D6, after the mock-up |
| 04 | next-in-line-from-the-plan | D | 3 | 03, f132-02 | D7 |
| 05 | map-opens-the-queue | D | 2 | 03, f199-04 | D8 |

## Before and after
- `/queue`
- `/`

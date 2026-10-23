# Milestone F5: steer from the phone, and the board

> **Status: planned** (2026-10-02), on [ADR 18](../adr/18-dashboard-writes.md) and [ADR 19](../adr/19-feature-board.md). The owner's priorities 2 and 3: a backlog of features, and reviewing from the dashboard. Its tickets can run beside F4's; some depend on F4 tickets by id.
> **State:** building · **Priority:** 4 · **Area:** factory

## Outcome
- From the phone, on the home Wi-Fi (`runner dashboard --lan`), the owner can:
  - sign off a milestone;
  - answer the 5-hour question (since F8, a switch: "use reserve");
  - queue a ticket from `.factory/tasks/later/`.

  Each is a request the runner carries out, as its console command would.
- An open dashboard page sends a browser notification when something needs the owner, and when all the work is done.
- Milestone docs carry a state and a priority (cards). Bugs are `bug-` tickets outside milestones. The runner picks by priority.
- The backlog is bug tickets, waiting in `.factory/tasks/later/` with priorities.
- **The board page** (`/board`, read-only), from the mock-up the owner accepted (2026-10-02): tickets 15–17.

## Decisions
- **D1 The request table** (ADR 18 item 2): migration `_V5` in `runner/metrics.py`.
  - Table `owner_requests`: `id`, `project_id`, `kind`, `subject`, `value`, `created`, `done` (ISO time or NULL), `result` (text or NULL); `dismissed` since F31 (`_V11`).
  - F5's kinds, as built. The planning room added its own since (F6 D1, F31); the whole list is `KINDS` in `factory_dashboard/requests.py`, each read in `runner/requests.py`.

    | kind | subject | value |
    |---|---|---|
    | `signoff` | the milestone key (full or short) | – |
    | `reserve` | `week` or `five_hour` | `on` / `off` |
    | `queue` | the ticket id | – |
    | `pause` | – | – |
    | `resume` | – | – |
    | `reorder` | – | a JSON list: the open cards' short keys and the open bug tickets' ids, first in line first (F15 D3) |

    `reserve` replaced the planned `five_hour` (yes or no) in F8 (ADR 22 item 4, f8-10).
  - `runner/metrics.py` owns `add_request(conn, project_id, kind, subject, value, created)` and `open_requests(conn, project_id)`. It also owns `finish_request(conn, request_id, done, result)`.
- **D2 Who applies requests:** `runner/requests.py`, `apply_requests(repo, db, now, state) -> list[str]` (one line per request done or left to wait; `state` is the run's `state.json`, which the switches and the pause change).
  - It calls `owner.signoff` and the `queue` command's function (`loop.move_to_ready`, f4-09), and never runs git directly for them.
  - The runner calls it at every pick. While a run waits for the owner (their 25%, or their resume), `take_switches` applies the requests that change `state.json` alone (`reserve`, `pause`, `resume`); the others wait for the pick. Every `runner` command calls it at start, so a request made while nothing runs is applied by the next command.
  - A request that commits (a sign-off, a queue) waits, still open, until the repo is on `main` (and clean, for a sign-off).
  - A request that fails is finished with its error as `result`, and never retried.
- **D3 The dashboard's write** (ADR 18 items 2–3): `POST /requests` in `factory_dashboard/requests.py`. It is the only route that opens the database for writing (`writable`, a second connection in `factory_dashboard/app.py`).
  - It requires the `HX-Request` header and a same-origin `Origin` or `Referer`, else 403; a kind outside `KINDS` is 400.
  - It answers with a small htmx partial, `factory_dashboard/templates/_partials/request.html`: "Asked: the runner will do it.", polling `GET /requests/{id}` every 5 s, then the result once done.
  - Worked example for the buttons (08, 09), in `docs/agents/developer.md`.
- **D4 Cards** (ADR 19 items 1 and 2b): a milestone doc's header blockquote may hold `**State:** <state> · **Priority:** <n> · **Area:** factory|product`.
  - States: idea, planning, ready, building, needs sign-off, done.
  - `runner/milestone.py` `card(key, text) -> Card(state, priority, area)`: a missing state is derived (done when "Status: done", else building), a missing priority is 100, and a missing area comes from the key's series (`f` factory, `m` product).
  - Synced to three new `milestones` columns, `state`, `priority` and `area`, in `_V6`.
  - **Who sets the state** (f5-07, 2026-10-13). The runner writes the doc's state only where the owner decides: planting writes idea, approving a plan ready (`approve_plan`), the sign-off done. Nothing writes planning, building or needs sign-off (the lead may, by hand), so F6, F8 and F9 said ready while they were built.
  - **The board derives the stage** from the card's thread and its tickets; the runner doesn't advance the doc. The first that holds:
    1. signed off (`milestones.status` is done) → harvested;
    2. state idea with no planning thread → seed, as the desk's seeds; state planning, or an idea a thread is about → sprouting;
    3. every ticket done and the review's sheet stored → ripe (needs sign-off), as the line's field and the desk have it since F50 D1;
    4. otherwise → planted (ready, or building); a planted card with a ticket started (a job on it, or it is running, done, escalated or blocked) says "growing" on itself. Growing was a column of its own until F154 D1 made it one Planted column in the runner's order.

    Set-aside and removed tickets count for none of these; a removed card is on no column.
    - Why not the runner: advancing the doc would be a commit on main at each first job and each last merge, and a second source for what the tickets already say. The doc's `building` stays valid (a card with no state derives to it, and a plan approved on a building card keeps it), but the board doesn't need it.
- **D5 Bug tickets** (ADR 19 items 2 and 2b): id `bug-<nn>-<slug>`, `milestone: bugs`, an optional `priority:` in frontmatter (default 50) and `area:` (factory or product, required on a bug). The ticket's area is stored in a new `tickets.area` column (`_V7`).
  - `bugs` is a standing key: never signed off, never reviewed. Checkpoints count its merges. It has a `milestones` row like any key, which is not a card.
  - `.factory/cards/bugs.md` explains it, with **State:** building.
- **D6 The pick** (ADR 19 item 3): `pick_next` takes the runnable ticket that is first by `run_order`: `(priority, milestone_order, id)`. A ticket's priority is its own `priority:`, else its milestone card's, else 100 (`task_priority`, all three in `runner/tasks.py`). The dashboard reads the same order from the database (`run_order` and `ticket_priority` in `factory_dashboard/queries.py`).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | requests-apply | L | 6 | f4-09 | D1, D2: the table, `apply_requests`, called at each pick, while waiting for an answer, and at each command's start |
| 02 | requests-route | L | 5 | 01 | D3: `POST /requests`, its guard and partial; the worked example |
| 03 | dashboard-lan | L | 2 | – | `runner dashboard --lan` binds to this machine's LAN address |
| 04 | cards | L | 5 | – | D4: state and priority in milestone docs, synced to the database |
| 05 | bug-tickets | L | 5 | – | D5: `bug-` tickets and the `bugs` key |
| 06 | priority-pick | L | 4 | 04, 05 | D6: the runner picks by priority |
| 07 | replan | L | 3 | 02, 06 | Check D1–D6 and tickets 08–11 and 15–17 against what 01–06 built; fix them; log it here |
| 08 | signoff-button | D | 3 | 07 | The planning page's "Sign off" button on a ripe milestone's own page too |
| 09 | queue-button | D | 3 | 07, f4-18 | A "Queue" button on each set-aside ticket |
| 10 | five-hour-buttons | – | – | – | Set aside: replaced by F8's reserve switches (f8-06, f8-14) |
| 11 | queue-priority | D | 2 | 07, 09, f9-05 | The set-aside tickets by priority, each with its own (the Overview's queue was done in f6-18) |
| 12 | notifications | L | 4 | – | Browser notifications on an open page: needs you, all work done |
| 13 | backlog-to-bugs | L | 3 | 05 | `docs/backlog.md` becomes bug tickets in `.factory/tasks/later/`, with priorities |

| 14 | factory-look | L | 5 | – | The mock-ups' look on every page: tokens, dark by default with a light variant (follows the system), fonts self-hosted |
| 15 | board-data | L | 5 | 07 | `board.py`: every milestone and bug ticket as a card, in its stage and priority order |
| 16 | board-page | L | 5 | 14, 15 | `/board`: the field, totals, search and kind filter; desktop and phone |
| 17 | card-page | L | 4 | 14, 15, 16, 08 | A milestone's page as its card: stage, priority, area, how it grew, tickets in run order |
| 18 | pause | L | 4 | 01, 02 | `pause` / `resume` requests: the runner finishes its job and holds; "Pause after this job" and "Resume" on Now (owner, 2026-10-03) |
| f3-08 | field-cards | D | 3 | 15 | Moved from F3: the line's field from the board's cards |

14 (factory-look) runs with F3 (`milestone: f3`), right after the line fixes (owner, 2026-10-03: "the small factory line fixes first, then the global redesign").

The picture: the board mock-up, <https://claude.ai/artifact/PzgTodVwvuQKqLvxphPLGu> (accepted by the owner, 2026-10-02), with its sources in `.factory/cards/f5-board-mockup/` for the tickets to read.

f5-07 (replan) also checks 15–17 against what 04–06 built.

## Replan
**f5-07 (2026-10-13)**, against f5-01 to f5-06 as merged (`6aafd8e`, `c2d8d9a`, `d71b15b`, `579b641`, `6bb360f`, `b236606`) and what F6, F8, F31 and F50 built on them since.
- **Outcome:** the 5-hour question is a switch since F8; the board's mock-up is accepted and its tickets written.
- **D1:** `five_hour` (yes or no) never reached a button: F8 replaced it with `reserve` (`week` or `five_hour`, on or off). The planning room's kinds are in `KINDS`; `dismissed` named.
- **D2:** `apply_requests` takes the run's state too; `read_answer` is gone, and a wait applies only the requests that change `state.json` (`take_switches`); a request that commits waits for `main`.
- **D3:** the partial's path and its poll named; a kind outside `KINDS` is 400. The worked example serves 08 and 09 (10 is set aside).
- **D4:** the card columns came in `_V6`, not `_V5` (`_V5` is the request table).
  - **Card states don't advance, decided:** the board derives a card's stage from its thread and its tickets; the runner doesn't advance the doc's state. Reasons in D4. This is the rule the line's field (`_field`) and the desk already follow for ripe (F50 D1), so the three agree.
  - Nothing writes `planning` either, so sprouting is "state planning, or an idea a planning thread is about", as the desk tells a seed from a card being planned.
- **D5:** `tickets.area` came in `_V7`; the `bugs` key has a `milestones` row that is not a card.
- **D6:** the functions named (`run_order`, `task_priority`), and the dashboard's copies of the order.
- **Who builds the board:** 15, 16 and 17 go to the lead. None is a one-template change on a lead-written function: 15 is the function itself (a new module, five stage rules across three tables), 16 a new page with a phone layout, 17 a page rebuilt, and the local model failed every ticket of that kind (F6: 0 of 5; f8-06, f8-07). The developers keep the small ones on top: 08 and 11 (one function and one template each), 09 (one template) and f3-08 (one function, on `board`).
- **Tickets:**
  - **08:** a "Sign off" button exists since F50, on a ripe card's planning page, and only once the review is written. The ticket's own rule ("no ticket left") would have offered a sign-off before the review. It now puts the same button, rule and three states (`_review`) on the milestone's page; the import cycle with `planning.py` named; the conftest added to its files.
  - **09:** right as written. Added: the partial's words, the runner's result, the button disabled as the request leaves (the owner, 2026-10-07), one place per row for the answer.
  - **10:** set aside on 2026-10-06 (`578bd25`) when ADR 22 item 4 replaced it; f8-06 and f8-14 built the switches. Its file in `.factory/tasks/later/` now says so, and that its `five_hour` request would be 400.
  - **11:** already built by f6-18 (the Overview's queue in the runner's order, each priority on Next in line, tested in `tests/factory_dashboard/test_overview.py`); a developer would have found its tests passing before any change. A headless job can't remove a ticket, so it is rewritten to what was left of the Outcome's "backlog with priorities": the Set aside table by priority, each ticket's shown. It waits for 09 and f9-05, which edit the same table.
  - **15:** the stage rules of D4, in order; the ticket states the database holds (`escalated`, `blocked` and `removed` were missing); removed cards and the `bugs` row left out; where a card's priority and area come from when its row has none; a bug has no merge time (its latest job's end); `board` takes `now`, for the running jobs.
  - **16:** the tokens rule and its test, the full key in a card's link, the layout check's name, the Board tab in Done when.
  - **17:** it waits for 08 (both edit `milestone.html`); the stage is the board's, not the doc's state; a link to the card's planning thread; the Milestones list keeps the only ↑ and ↓ of the cards and the trends, so the board links to it once its tab goes; `board.py`, `board.html` and `test_board.py` added to its files.
- **Seen, not changed:**
  - `.factory/tasks/ready/f3-08-field-cards.md` (not in this ticket's files) is right as written. The line's field counts set-aside tickets as seeds and ideas as planting, where the board counts ideas as seeds; f3-08 is the ticket that makes them one.
  - f5-11's name no longer says what it does (an id can't change). **Suggested fix:** none needed; the table above and its Goal say it.

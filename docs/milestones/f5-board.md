# Milestone F5: steer from the phone, and the board

> **Status: planned** (2026-10-02), on [ADR 18](../adr/18-dashboard-writes.md) and [ADR 19](../adr/19-feature-board.md). The owner's priorities 2 and 3: a backlog of features, and reviewing from the dashboard. Its tickets can run beside F4's; some depend on F4 tickets by id.
> **State:** building · **Priority:** 3 · **Area:** factory

## Outcome
- From the phone, on the home Wi-Fi (`runner dashboard --lan`), the owner can:
  - sign off a milestone;
  - answer the 5-hour question;
  - queue a ticket from `tasks/later/`.

  Each is a request the runner carries out, as its console command would.
- An open dashboard page sends a browser notification when something needs the owner, and when all the work is done.
- Milestone docs carry a state and a priority (cards). Bugs are `bug-` tickets outside milestones. The runner picks by priority.
- The backlog is bug tickets, waiting in `tasks/later/` with priorities.
- **The board page** (`/board`, read-only) waits for its mock-up. Its tickets are written once the owner is happy with it.

## Decisions
- **D1 The request table** (ADR 18 item 2): migration `_V5` in `runner/metrics.py`.
  - Table `owner_requests`: `id`, `project_id`, `kind`, `subject`, `value`, `created`, `done` (ISO time or NULL), `result` (text or NULL).
  - The kinds:

    | kind | subject | value |
    |---|---|---|
    | `signoff` | the milestone key | – |
    | `five_hour` | – | `yes` / `no` |
    | `queue` | the ticket id | – |

  - `runner/metrics.py` owns `add_request(conn, project_id, kind, subject, value, created)` and `open_requests(conn, project_id)`. It also owns `finish_request(conn, request_id, done, result)`.
- **D2 Who applies requests:** `runner/requests.py`, `apply_requests(repo, db, now) -> list[str]` (one line per request done).
  - It calls `owner.signoff`, the `queue` command's function (f4-09) and the 5-hour answer, and never runs git directly.
  - The runner calls it at every pick, and `read_answer` polls it while it waits for an answer. Every `runner` command calls it at start, so a request made while nothing runs is applied by the next command.
  - A request that fails is finished with its error as `result`, and never retried.
- **D3 The dashboard's write** (ADR 18 items 2–3): `POST /requests` in `factory_dashboard/requests.py`. It is the only route that opens the database for writing (a second, writable connection in `factory_dashboard/app.py`).
  - It requires the `HX-Request` header and a same-origin `Origin` or `Referer`, else 403.
  - It answers with a small htmx partial: "asked: the runner will do it", then the result once done.
  - Worked example for the buttons (08–10).
- **D4 Cards** (ADR 19 items 1 and 2b): a milestone doc's header blockquote may hold `**State:** <state> · **Priority:** <n> · **Area:** factory|product`.
  - States: idea, planning, ready, building, needs sign-off, done.
  - `runner/milestone.py` `card(key, text) -> Card(state, priority, area)`: a missing state is derived (done when "Status: done", else building), a missing priority is 100, and a missing area comes from the key's series (`f` factory, `m` product).
  - Synced to three new `milestones` columns, `state`, `priority` and `area`, in `_V5`.
- **D5 Bug tickets** (ADR 19 items 2 and 2b): id `bug-<nn>-<slug>`, `milestone: bugs`, an optional `priority:` in frontmatter (default 50) and `area:` (factory or product, required on a bug). The ticket's area is stored in a new `tickets.area` column.
  - `bugs` is a standing key: never signed off, never reviewed. Checkpoints count its merges.
  - `docs/milestones/bugs.md` explains it, with **State:** building.
- **D6 The pick** (ADR 19 item 3): `pick_next` sorts the runnable tickets by `(priority, milestone_order, id)`. A ticket's priority is its own `priority:`, else its milestone card's, else 100.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | requests-apply | L | 6 | f4-09 | D1, D2: the table, `apply_requests`, called at each pick, while waiting for an answer, and at each command's start |
| 02 | requests-route | L | 5 | 01 | D3: `POST /requests`, its guard and partial; the worked example |
| 03 | dashboard-lan | L | 2 | – | `runner dashboard --lan` binds to this machine's LAN address |
| 04 | cards | L | 5 | – | D4: state and priority in milestone docs, synced to the database |
| 05 | bug-tickets | L | 5 | – | D5: `bug-` tickets and the `bugs` key |
| 06 | priority-pick | L | 4 | 04, 05 | D6: the runner picks by priority |
| 07 | replan | L | 3 | 02, 06 | Check D1–D6 and tickets 08–12 against what 01–06 built; fix them; log it here |
| 08 | signoff-button | D | 3 | 07 | A "Sign off" button on a milestone page whose tickets are all done |
| 09 | queue-button | D | 3 | 07, f4-18 | A "Queue" button on each set-aside ticket |
| 10 | five-hour-buttons | D | 3 | 07 | Yes and No buttons on the 5-hour Needs-you item |
| 11 | queue-priority | D | 2 | 07, f4-10 | The Overview's queue in the new order, with each ticket's priority |
| 12 | notifications | L | 4 | – | Browser notifications on an open page: needs you, all work done |
| 13 | backlog-to-bugs | L | 3 | 05 | `docs/backlog.md` becomes bug tickets in `tasks/later/`, with priorities |

| 14 | factory-look | L | 5 | – | The mock-ups' look on every page: tokens, dark by default with a light variant (follows the system), fonts self-hosted |
| 15 | board-data | D | 5 | 07 | `board.py`: every milestone and bug ticket as a card, in its stage and priority order |
| 16 | board-page | D | 5 | 14, 15 | `/board`: the field, totals, search and kind filter; desktop and phone |
| 17 | card-page | D | 4 | 14, 15 | A milestone's page as its card: stage, priority, area, how it grew, tickets in run order |

The picture: the board mock-up, <https://claude.ai/artifact/PzgTodVwvuQKqLvxphPLGu> (accepted by the owner, 2026-10-02), with its sources in `docs/milestones/f5-board-mockup/` for the tickets to read.

f5-07 (replan) also checks 15–17 against what 04–06 built.

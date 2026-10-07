# Milestone F6: the planning room

> **Status: planned** (2026-10-03), on [ADR 20](../adr/20-planning-room.md) (Proposed until the owner accepts it). **State:** building · **Priority:** 1 · **Area:** factory
> The owner's goal: "do from the system what we did in this long chat, async with a nice UI". Picture: <https://claude.ai/artifact/UNELSzF5iF5RccjVJiWZzx>, sources in `docs/milestones/planning-room-mockup/`, with two changes from the owner: "planning goes first" merges into "The factory now", and every point is agreed by default (only Comment… on what to change or ask).
> Builds on F5's requests (f5-01, f5-02), cards (f5-04), notifications (f5-12) and the look (f5-14), by its tickets' dependencies.

## Outcome
- The owner plants ideas, asks about them, and reviews the lead's answers and proposals from `/planning`, on a phone too, while the factory works.
- **Planner jobs go before every other lead job.** Replies come as numbered points with actions; the owner comments only where they disagree or have a question.
- **The lead proposes, the owner approves:** ADRs, mock-ups, plans and tickets are drafts on `plan/<card>` until approved. Approving merges them and queues the tickets.
- The Overview's Needs you and the top bar say when the desk has something, and a notification comes with each reply.

## Decisions
- **D1 Tables and requests:**
  - **Tables:** `planner_threads` (`id`, `project_id`, `card` or `general`, `session_id`, `created`) and `planner_messages` (`id`, `thread_id`, `author` (owner | lead), `at`, `text`, `points` JSON, `proposals` JSON, `job_id`).
  - **Request kinds** (`owner_requests`, F5):

    | kind | subject | value | its result when it worked |
    |---|---|---|---|
    | `plan_message` | the thread: `general` or the card's short key (`f7`) | JSON `{"text": …, "comments": {"2": …}}`, text or a comment needed | `queued for the lead` |
    | `plant` | none, or a general seed `general/<id>` (f6-04) | JSON `{"title", "thoughts", "area"}` (area optional: factory); a seed's optional `{"area"}` | `planted docs/milestones/…` |
    | `send_back` | the proposal: `<thread>/<proposal id>` | as `plan_message`, comments by key point number | `queued for the lead` |
    | `accept_adr` | the thread (the card's key) | the ADR's number (`23`, from the proposal's path `docs/adr/23-….md`) | `accepted docs/adr/…` |
    | `approve_plan` | the thread (the card's key, or `general` for its merges) | – | `approved plan/…: queued …`, then `; merged F12 into F10` per merge; `approved: merged …` with no branch |
    | `drop_seed` (f6-17) | the idea card's short key (`f11`) | – | `removed docs/milestones/f11-….md` |

  - **`drop_seed`** (f6-17, the owner's "Remove seed" on an idea card's thread page, after a confirm step): refused, main unchanged, when the card isn't `**State:** idea` or a ticket in `tasks/` (`tasks/*/f11-*.md`) belongs to it. Otherwise one commit, `F11 removed by the owner`, `git rm`s its doc alone; its thread (if any) gets the lead message "Removed by the owner on <date>.", its open `planner` rows are done and its `planning` owner item resolves. A `plan/f11` branch is left as it is.
  - **Gone files leave the board (f6-17):** a card's `milestones` row whose doc is gone from `docs/milestones/` (by short key) gets `state` `removed`, kept rather than deleted, as jobs, tickets and findings may point at it. `sync_cards` does it each session; a merge and a `drop_seed` do it at once. A row with no `state` (never a card) is left alone. `sync_tickets` marks `removed` any ticket row whose file is in no `tasks/` folder, whatever its state but `done` (history stays).

  - **A thread's `card`** is the card's short key (`f7`, `runner.tasks.short_key`) or `general`, never `milestones.key` (`f7-planning-room`).
  - **A pending reply:** each `plan_message` queues a `work_queue` row of kind `planner`, subject `<thread>#<request id>` (`planner.row_subject`), open (`metrics.open_jobs`) until the lead's reply is stored.
  - **A reply** raises an owner item of kind `planning`, subject the thread, resolved by the owner's next message there.
  - **The dashboard's `POST /requests`** takes these five kinds once f6-11 adds them to `KINDS` in `factory_dashboard/requests.py` (protected); until then it refuses them.

- **D2 The reply block:** the planner ends each reply with a fenced `json` block:
  - `points`: a list of `{n, title, answer, action}`;
  - `proposals`: a list of `{id, kind (adr | mockup | plan | seed | replan | merge), title, path, key_points: [{n, title, text, flag}]}`, and a merge's `into`.
  - A `replan` (owner, 2026-10-03: "direct a milestone as it's happening… trigger a replan from the result of the chat") changes the ready tickets of a milestone that is running. f5-18's pause holds the line while the owner and the lead talk, and approving the proposal applies it and resumes. f6-03 handles it as a `plan`.
  - A `merge` (f6-12, owner 2026-10-06: "whenever I plant an idea… the lead should detect it, suggest closing one of the duplicates") says a card repeats another: `{id, kind: "merge", title, path: "docs/milestones/<duplicate>.md", into: "<kept card's short key>", key_points}`, the key points saying what moves where. `parse_reply(text, planner.cards(repo))` refuses one without `into`, naming a card with no doc on main, or merging a card into itself. Both prompts ask the planner to check the idea, planning and ready cards and the other threads (named in the prompt) first. A planted title that is already a card is still refused (`card_named`): a merge covers the same idea in other words.
  - **As built (f6-13):** a card's plan branch may also carry edits to that card's own `tasks/ready/<card>-*.md` tickets: changed, added, or set aside (moved to `tasks/later/`). `planner.is_draft(path, card)` takes the card; the planner job may edit `planner.drafts(card)`, and the runner commits them. `approve_plan` takes them only while the thread's open proposals hold a `replan`, and refuses, naming the path and why, nothing applied: another milestone's ticket, the running one (`in_flight` in `var/runs/state.json`), a ready ticket removed but not set aside, anything in `tasks/done/`, or a ready edit with no `replan`. Pre-flight runs on every ticket it adds, changes or queues first; any problem refuses the approval. A ticket set aside stays in `tasks/later/`. A building card keeps its state. Once applied, a pause the owner set is lifted (its usage event ends), and the result says `resumed`: `approved plan/f7: queued f7-03-c; changed f7-01-a; set aside f7-02-b; resumed`. The planner prompt says what a `replan` may change and to suggest a pause when the line could start a ticket being changed; f6-14 lets planner jobs and approvals run while paused.

  `runner/planner.py` owns `parse_reply(text) -> Reply` and checks it.
- **D3 Sessions:** a thread's first planner job starts a Claude session; later ones `--resume` it. The session id lives on the thread.
- **D4 The plan branch:** `plan/<card key>`, created from main at the thread's first proposal and kept up to date with main before each planner job. Drafts only (`docs/`, `tasks/later/`, and for a `replan` the card's own `tasks/ready/` tickets, D2). Approval merges it (f6-03).
  - **As built:** the branch is made at the card's first planner job and deleted when that job drafted nothing. Mock-ups go in `docs/milestones/<card>-mockup/`.
  - An ADR draft reaches main at `accept_adr`; everything else on the branch (plans, mock-ups, tickets) reaches it at `approve_plan`, all at once. Before that, a draft exists only on the branch, and the runner checks the branch out during a planner job.
  - So the dashboard reads a draft from git, never from the working tree: `planner.draft(repo, thread, path)` (f6-11), the file on `plan/<card>` while it exists, else main's.
  - **Merges (f6-12):** `approve_plan` on a thread also applies the `merge` proposals of its latest lead message that lists proposals, in the same commit as its plan (`F10 plan approved by the owner; F12 merged into F10`), or alone when the thread has no branch, the general thread included (`F12 merged into F10 by the owner`; result `approved: merged F12 into F10`). Each one appends the duplicate's Notes (every section when it has none, headings demoted, quoted lines escaped) to the kept card's Notes under `### From F12: <title> (merged by the owner on <date>)`, and `git rm`s the duplicate's doc. After the commit, the duplicate's thread gets a lead message pointing to `/planning/<kept>` and its `planning` owner item is resolved. Refused, main unchanged: a duplicate with tickets in `tasks/`, a card with no doc, or a thread whose own card merges away while its plan branch has drafts (send it back). `send_back` works as for any proposal. Nothing changes before approval.
- **D5 Planting:** the next free key in the area's series (`f` factory, `m` product), the slug from the title, **State:** idea. A general-thread `seed` proposal plants the same way when approved.
- **D6 The desk** (`factory_dashboard/planning.py`, `desk(conn, project)`), one list for the planning page, Needs you and the top bar's count. Each item has its group, its words and its link (`/planning/<thread>` or `/planning/<thread>/proposals/<id>`):
  - threads whose last message is the lead's (your answers wanted; the same threads as the open `planning` owner items);
  - open proposals: those in a thread's latest lead message that lists proposals, unless an owner request about one was made after that message and is still pending or worked (D1's results). About a proposal means: its `send_back`; for an `adr`, the card's `accept_adr` with its number; for a `plan`, `mockup`, `replan` or `merge`, the card's `approve_plan`; for a `seed`, its `plant` `general/<id>`. A refused request leaves it open;
  - ripe cards: every ticket done and not signed off, as the line's field has them (`_field` in `factory_dashboard/line.py`);
  - idea cards with no thread: `milestones.state` is `idea` and no `planner_threads` row has its short key.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | planner-threads | L | 7 | f5-01, f5-04 | D1, D3: threads, messages, `plan_message`; planner jobs go first, may use the owner's 25% |
| 02 | planner-prompt | L | 5 | 01 | How the planner plans (numbered points, drafts on the plan branch, nothing queued unapproved) |
| 03 | proposals-approval | L | 7 | 02 | `send_back`, `accept_adr`, `approve_plan`: merge drafts, pre-flight, queue tickets |
| 04 | plant-ideas | L | 4 | 01 | `plant`: a seed card without Claude; seeds from the general thread |
| 05 | replan | L | 3 | 03, 04 | Check D1–D6 and 06–10 against what 01–04 built |
| 11 | planning-requests | L | 3 | 05 | Added by the replan: the dashboard may post D1's five kinds; `planner.draft` reads a draft from git |
| 06 | desk-page | D | 5 | 05, 11 | `/planning`: the factory now, the lead's window, the desk, Plant an idea |
| 07 | thread-page | D | 6 | 06 | A thread: messages, points agreed by default with Comment…, Send, proposals |
| 08 | proposal-review | D | 5 | 06 | A proposal's key points, Send back / Accept ADR / Approve plan, mock-ups in a sandbox |
| 09 | needs-you-desk | D | 3 | 06 | Needs you and "Planning · N" from the desk |
| 10 | planning-phone | D | 4 | 07, 08 | One point at a time, the Send button pinned at the bottom |
| 12 | merge-duplicates | L | 6 | 08 | The planner spots duplicate cards and threads and proposes a `merge`; approval closes one and keeps talking in the other (owner, 2026-10-06) |
| 13 | replan-edits-ready | L | 6 | 12, f5-18, 14 | A `replan` changes its milestone's ready tickets, applied on approval while paused: the "Later" item, brought forward (owner, 2026-10-06) |
| 14 | talk-while-paused | L | 4 | f5-18 | While paused, the owner's requests apply and planner jobs run; nothing else starts (ADR 22 item 5 ⚑, owner 2026-10-07) |
| 15 | queue-message | D | 3 | – | Next in line: a planning row shows the message's start (whole on hover) and links to its thread; pending plants are rows |
| 16 | top-bar-status | L | 4 | 14 | Every page's top bar: running, idle, pausing, paused or waiting, a big Pause/Resume, the Planning count, "Turn on notifications" |
| 17 | drop-seed | L | 4 | 14 | `drop_seed`: Remove seed on an idea's page; cards and tickets whose file is gone leave the dashboard |
| 18 | priority-buttons | L | 5 | 17 | `priority`: ↑/↓ on Next in line's tickets and on Milestones, applied as a commit |
| 19 | replan | L | 3 | 13, 16, 18 | Check D1–D6 against 13–21; walk the steering loop end to end |
| 20 | desk-coming | D | 3 | – | The desk's "Coming" group, dashed orange: pending plants, threads waiting for the lead |
| 21 | sent-message | D | 3 | – | A sent message shows at once as the owner's, "Sent", and the Send box goes |

**Priority 1 (owner, 2026-10-06):** steering and planning from this room comes first, so the owner stops the factory less often to plan in a terminal. f5-12 (notifications, for 09) and f5-18 (pause, for 13) carry `priority: 1` too.

**The owner's notes of 2026-10-07** (after the first pause from the dashboard) are 14–21: steering from the room still needed a terminal session, because a pause held the planner too, and nothing the owner asked for showed until the runner's next pick. Routing: developer tickets where the change is small, unprotected and follows an example in the code; the lead's where it wires something new (owner, 2026-10-07).

Later: cancel or edit a message the lead hasn't picked up yet (owner, 2026-10-07); parallel planner jobs beside developers (with parallel developers); a live, streaming reply; a preview of the work ahead; the dashboard showing a `replan`'s edited ready ticket (`planner.draft` reads only `docs/` and `tasks/later/`). A `replan` that edits ready tickets is built (f6-13, D2).

## Replan
**f6-05 (2026-10-06)**, against f6-01 to f6-04 as merged (`3962439`, `0518a23`, `00a90a8`, `50a77af`):
- **A gap, now a ticket:** the dashboard's `POST /requests` takes only `signoff`, `reserve` and `queue` (`KINDS` in `factory_dashboard/requests.py`, protected). f6-06 to f6-08 would have posted kinds it refuses with a 400, and developers can't edit that file. f6-11 (lead) adds the five, and f6-06 now waits for it.
- **A gap, now in f6-11:** drafts live only on `plan/<card>` until approved, and the runner checks that branch out during planner jobs. f6-08's mock-up route would have read the working tree, so it would show nothing, or the wrong branch's file, while the owner reviews. `planner.draft` (f6-11) reads it from git.
- **D1:** each kind's exact subject, value and result, as `runner/requests.py` reads them; threads keyed by the short key, not `milestones.key`; how a pending reply and a reply's `planning` owner item show in the database.
- **D2:** a `replan` can't edit ready tickets yet, and f5-18 (pause) isn't built. Recorded as built, with a suggested fix under "Later". 06 to 10 don't rely on it.
- **D4:** when the branch is made and dropped, where mock-ups go, and what reaches main at `accept_adr` and at `approve_plan`.
- **D6:** nothing stores a proposal's state, so "open" is defined from the requests about it; ripe and idea-with-no-thread named by their columns and functions; each desk item has words and a link.
- **Tickets:**
  - 06: the facts above; it adds the Planning tab (base.html had none); the existing layout check (`layout_problems`).
  - 07: the message rows' JSON shapes, the `plan_message` value, the pending row.
  - 08: each button's subject and value; `approve_plan` approves the whole branch; a seed's "Plant it"; "Proposed" read from main's ADR; the mock-up route reads through `planner.draft`.
  - 09: Needs you already lists each `planning` owner item, so the desk entry replaces them rather than doubling them.
  - 10: unchanged.

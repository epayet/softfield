# Milestone F6: the planning room

> **Status: planned** (2026-10-03), on [ADR 20](../adr/20-planning-room.md) (Proposed until the owner accepts it). **State:** ready · **Priority:** 3 · **Area:** factory
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
    | `approve_plan` | the thread (the card's key) | – | `approved plan/…: queued …` |

  - **A thread's `card`** is the card's short key (`f7`, `runner.tasks.short_key`) or `general`, never `milestones.key` (`f7-planning-room`).
  - **A pending reply:** each `plan_message` queues a `work_queue` row of kind `planner`, subject `<thread>#<request id>` (`planner.row_subject`), open (`metrics.open_jobs`) until the lead's reply is stored.
  - **A reply** raises an owner item of kind `planning`, subject the thread, resolved by the owner's next message there.
  - **The dashboard's `POST /requests`** takes these five kinds once f6-11 adds them to `KINDS` in `factory_dashboard/requests.py` (protected); until then it refuses them.

- **D2 The reply block:** the planner ends each reply with a fenced `json` block:
  - `points`: a list of `{n, title, answer, action}`;
  - `proposals`: a list of `{id, kind (adr | mockup | plan | seed | replan), title, path, key_points: [{n, title, text, flag}]}`.
  - A `replan` (owner, 2026-10-03: "direct a milestone as it's happening… trigger a replan from the result of the chat") changes the ready tickets of a milestone that is running. f5-18's pause holds the line while the owner and the lead talk, and approving the proposal applies it and resumes. f6-03 handles it as a `plan`.
  - **As built (f6-05):** a plan branch holds only `docs/` and `tasks/later/` (`planner.is_draft`), and f5-18 is still in `tasks/ready/`. So today a `replan` can change docs and add tickets, which `approve_plan` queues; it can't edit a ready ticket, and nothing pauses. See "Later".

  `runner/planner.py` owns `parse_reply(text) -> Reply` and checks it.
- **D3 Sessions:** a thread's first planner job starts a Claude session; later ones `--resume` it. The session id lives on the thread.
- **D4 The plan branch:** `plan/<card key>`, created from main at the thread's first proposal and kept up to date with main before each planner job. Drafts only (`docs/`, `tasks/later/`). Approval merges it (f6-03).
  - **As built:** the branch is made at the card's first planner job and deleted when that job drafted nothing. Mock-ups go in `docs/milestones/<card>-mockup/`.
  - An ADR draft reaches main at `accept_adr`; everything else on the branch (plans, mock-ups, tickets) reaches it at `approve_plan`, all at once. Before that, a draft exists only on the branch, and the runner checks the branch out during a planner job.
  - So the dashboard reads a draft from git, never from the working tree: `planner.draft(repo, thread, path)` (f6-11), the file on `plan/<card>` while it exists, else main's.
- **D5 Planting:** the next free key in the area's series (`f` factory, `m` product), the slug from the title, **State:** idea. A general-thread `seed` proposal plants the same way when approved.
- **D6 The desk** (`factory_dashboard/planning.py`, `desk(conn, project)`), one list for the planning page, Needs you and the top bar's count. Each item has its group, its words and its link (`/planning/<thread>` or `/planning/<thread>/proposals/<id>`):
  - threads whose last message is the lead's (your answers wanted; the same threads as the open `planning` owner items);
  - open proposals: those in a thread's latest lead message that lists proposals, unless an owner request about one was made after that message and is still pending or worked (D1's results). About a proposal means: its `send_back`; for an `adr`, the card's `accept_adr` with its number; for a `plan`, `mockup` or `replan`, the card's `approve_plan`; for a `seed`, its `plant` `general/<id>`. A refused request leaves it open;
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

Later: parallel planner jobs beside developers (with parallel developers); a live, streaming reply; a preview of the work ahead; a `replan` that edits ready tickets under f5-18's pause (suggested: a lead ticket once f5-18 is done, letting a `replan`'s branch carry edits to its milestone's `tasks/ready/` tickets that `approve_plan` applies while paused).

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

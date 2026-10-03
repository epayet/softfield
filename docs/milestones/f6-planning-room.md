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

    | kind | subject | value |
    |---|---|---|
    | `plan_message` | the thread | `{text, comments: {n: text}}` |
    | `plant` | – | `{title, thoughts, area}` |
    | `send_back` | the proposal | its comments |
    | `accept_adr` | the card | the ADR number |
    | `approve_plan` | the card | – |

- **D2 The reply block:** the planner ends each reply with a fenced `json` block:
  - `points`: a list of `{n, title, answer, action}`;
  - `proposals`: a list of `{id, kind (adr | mockup | plan | seed | replan), title, path, key_points: [{n, title, text, flag}]}`.
  - A `replan` (owner, 2026-10-03: "direct a milestone as it's happening… trigger a replan from the result of the chat") changes the ready tickets of a milestone that is running. f5-18's pause holds the line while the owner and the lead talk, and approving the proposal applies it and resumes. f6-03 handles it as a `plan`; f6-05 checks this against what 01–04 built.

  `runner/planner.py` owns `parse_reply(text) -> Reply` and checks it.
- **D3 Sessions:** a thread's first planner job starts a Claude session; later ones `--resume` it. The session id lives on the thread.
- **D4 The plan branch:** `plan/<card key>`, created from main at the thread's first proposal and kept up to date with main before each planner job. Drafts only (`docs/`, `tasks/later/`). Approval merges it (f6-03).
- **D5 Planting:** the next free key in the area's series (`f` factory, `m` product), the slug from the title, **State:** idea. A general-thread `seed` proposal plants the same way when approved.
- **D6 The desk** (`factory_dashboard/planning.py`, `desk(conn, project)`), one list for the planning page, Needs you and the top bar's count:
  - threads whose last message is the lead's (your answers wanted);
  - open proposals;
  - ripe cards;
  - idea cards with no thread.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | planner-threads | L | 7 | f5-01, f5-04 | D1, D3: threads, messages, `plan_message`; planner jobs go first, may use the owner's 25% |
| 02 | planner-prompt | L | 5 | 01 | How the planner plans (numbered points, drafts on the plan branch, nothing queued unapproved) |
| 03 | proposals-approval | L | 7 | 02 | `send_back`, `accept_adr`, `approve_plan`: merge drafts, pre-flight, queue tickets |
| 04 | plant-ideas | L | 4 | 01 | `plant`: a seed card without Claude; seeds from the general thread |
| 05 | replan | L | 3 | 03, 04 | Check D1–D6 and 06–10 against what 01–04 built |
| 06 | desk-page | D | 5 | 05 | `/planning`: the factory now, the lead's window, the desk, Plant an idea |
| 07 | thread-page | D | 6 | 06 | A thread: messages, points agreed by default with Comment…, Send, proposals |
| 08 | proposal-review | D | 5 | 06 | A proposal's key points, Send back / Accept ADR / Approve plan, mock-ups in a sandbox |
| 09 | needs-you-desk | D | 3 | 06 | Needs you and "Planning · N" from the desk |
| 10 | planning-phone | D | 4 | 07, 08 | One point at a time, the Send button pinned at the bottom |

Later: parallel planner jobs beside developers (with parallel developers); a live, streaming reply; a preview of the work ahead.

# Milestone F84: Coming says which reply the lead is writing, and when each other one comes

> **State:** ready · **Priority:** 3 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
when the planner is replying to a thread or working on a proposal, it's not clear which one. all boxes just say something like 'the lead is typing its reply', how to make it a bit nicer?

## What happens today (from the code and the database, 2026-10-26)
- `_next_reply` in `factory_dashboard/planning.py` says "the lead is writing its reply now" as soon as **any** planner job runs, without asking which thread it is on. Coming (`coming`, same file) calls it once per waiting thread, so on 2026-10-26 at 23:33 all 30 Coming boxes read "waiting for the lead · the lead is writing its reply now" while only F84's was being written (job 1391); the 29 others were still in line.
- The thread page's "Next for the lead · …" line (`thread.html`, `#waiting`) uses the same words, so every waiting thread claims it is being answered.
- The Planning room's "The factory now" tile leaves planner jobs out (`factory_now`: `working = [j for j in jobs if j.role != PLANNER]`), so it said "Nothing running right now." while the lead was writing.
- Coming's order is the database's (threads by id, then plants), not the order the lead answers in.
- What is needed is already stored: a running planner job's queue row points at it (`work_queue.started_job`), its `subject` is `<thread>#<message>` (`f84#778`), and the runner answers planner rows oldest first (`dispatch.plan`: `created`, then `id`). A reply takes 3.3 min on average (the last 10 on Opus); `_typical` already averages it.
- A comment on a proposal is a message on the card's thread, so "working on a proposal" is the same job: naming the thread names it.

## Outcome
In the Planning room, the one thread the lead is writing in says so, plainly and on top; every other waiting thread says its place in line and about when its reply comes.

## Done when
- With a reply being written and others waiting, Coming lists the thread being answered first, marked "Writing now", with "the lead is writing this reply · 2 min in, about 1 min left"; the next ones read "next, after F84's reply · about 1 min", "3rd in line · about 4 min"…, in the order the lead takes them.
- The thread being answered shows the same words in its "Next for the lead" line; another waiting thread shows its place.
- The "The factory now" tile names the reply being written, linked to its thread, and how many replies wait after it and about how long for all of them.
- A held reply (Claude's limit) and a plant the runner hasn't picked up yet read as today.
- To test: on `/planning`, write on two or three cards' threads in a row, and watch Coming and each thread page while the first is answered; on a phone too.

## Decisions
- **D1 One function places each waiting thread.** `reply_line(conn, project_id, now) -> dict[str, Place]` in `factory_dashboard/planning.py`: for each thread with an open planner row, whether it is being written (its row's `started_job` is a live running job), or its place among the rows not started, in `dispatch.plan`'s order (`queued_jobs` in `factory_dashboard/overview.py` is the example). The desk's Coming, the thread page and the tile all read it; `_next_reply` takes a thread and uses it, and no longer says "writing its reply now" for a thread that isn't.
- **D2 The estimate** is the running job's time left (`_typical` minus elapsed, as today) plus `_typical` of a planner reply for each reply ahead; rounded with `ago`, "about" in front, "any minute now" under a minute. No estimate without a typical (as today: "after <job>").
- **D3 The words**, on the box and on the thread:
  - being written: "the lead is writing this reply · 2 min in, about 1 min left"; when its queue row's reason is "a ticket blocked on …", "the lead is looking at the blocked ticket · 2 min in…";
  - first in line: "next, after F84's reply · about 1 min" (the thread's short key), or "next, after f132-02-overview-live-every-project · about 12 min" when a ticket job runs, as today;
  - later: "3rd in line · about 4 min";
  - held for a Claude limit, and plants with no queue row yet: today's words.
- **D4 Coming's order** is the line's: the box being written first, then by place, then the plants and messages the runner hasn't picked up, then the rest as today.
- **D5 The box being written** gets a plate label "Writing now" (display type, Opus's colour `--opus`, which is the planner's agent) and a 3px left edge in the same colour; its words take `--opus` too. It is a status, so it is the agent's colour, not the hazard stripe; it doesn't blink. The others keep today's plate. A thin bar under the words, labelled "2 of about 3 min", is the calmer-or-bolder choice the mock-up shows; it is in the ticket (the owner can drop it).
- **D6 The tile** reads "Writing now: **F84**, <title> · 2 min in" (the key links to `/planning/f84`) and, under it, "Then 29 replies in line, about 1.6 h for all." The ticket job line ("Running f132-02…") stays above when one runs. F62 (Now, the top bar and Next in line name the card a review works on), still a draft, names reviews and checkpoints elsewhere; this card owns the planner's words in the Planning room only.
- **D7 Developer ticket.** `factory_dashboard/` is not protected; `queued_jobs` and `_next_reply` are the examples.

Picture: [`f84-mockup/coming-says-which.html`](f84-mockup/coming-says-which.html).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | coming-says-which | D | 3 | – | D1–D6: Coming, the thread's line and the tile |

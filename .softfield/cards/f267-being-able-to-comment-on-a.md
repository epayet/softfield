# Milestone F267: Add notes to a thread while the lead is still writing its reply

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
Being able to comment on a thread even though the lead is replying right now would be helpful even if it looks at it after it finishes what it's doing. In normal Claude chats you can steer it while it's doing something. It might not be up to that point but at least if I forgot something I can keep adding notes in the same thread that will be looked at at some point

### From F310: On this thread:… (merged by the lead on 2026-11-26)
On this thread: http://192.168.178.34:8765/planning/m14?project=travel-companion

I asked something and then added a note. I thought I would get one response that combines my 2 asks but I had to click earlier threads to see the response of one of them. 
Also, does that mean it did 2 rounds of planning or was it combined but formatted as two answers? 2 separate rounds sounds badly innfficiient

## What happens today (from the code, 2026-11-18)
- The thread page hides its message box whenever the lead owes a reply: `{% if not next_reply … %}` around `#reply` in `factory_dashboard/templates/thread.html`. While F267's first reply was written (job 2369), `/planning/f267` showed "Next for the lead · the lead is writing this reply" and no box at all.
- The runner already takes a second message: each `plan_message` becomes its own `planner` row (`_plan_message` in `runner/requests.py`), and a note sent during a job waits as a request until the runner's next pick, editable and cancellable meanwhile (F14). Only the page stops it.
- Each row is answered by its own job (`run_planner` in `runner/loop.py`), so three notes sent while the lead writes would be three more replies, the first written without seeing the other two. A planner reply costs about $3.50 (the average of 158 since 1 Nov).
- True steering, changing a reply while it is written, isn't possible as jobs run: a headless `claude -p` job gets its prompt once.

## Outcome
You can always write on a thread. A note sent while the lead is writing waits on the thread, marked as on its way, and every note waiting when the lead next starts on that thread is answered together, in one reply.

## Done when
- With the lead writing a reply on a thread, its page still has the box, labelled "Add a note · the lead reads it after this reply", with an "Add note" button.
- The note shows at once, dashed, "Sent · the lead reads it after this reply", and can be edited or cancelled until the runner takes it (as F14's waiting messages).
- Three notes sent during one reply get one reply after it, which answers all three; the thread then has one lead message, not three.
- The comment boxes on points still show only when nothing waits on the thread (they'd comment on points the lead is replacing).
- To test: on `/planning`, send a message on a card, and while "the lead is writing this reply" shows, add two notes; check the next reply answers both, on a phone too.

## Decisions
- **D1 The box is always there.** `thread.html` draws `#reply` whatever `next_reply` says (a card merged away still has none). While the lead owes a reply, its label reads "Add a note · the lead reads it after this reply", its button "Add note", and its aside "Every note sent before the lead starts again goes in one reply." A note waiting while the lead writes this thread's reply reads "Sent · the lead reads it after this reply" (today "Sent · the runner picks it up at its next pick"). Nothing else on the page changes: "Next for the lead" stays on top, and the point comment boxes keep their `next_reply is none` rule. Picture: [`f267-mockup/note-while-writing.html`](f267-mockup/note-while-writing.html).
- **D2 One reply for every waiting note.** When `run_planner` starts on a thread's owner message, every other open `planner` row of the same thread that hasn't started, and is the owner's (not a runner's look at a blocked ticket, `planner.look_of`), joins the job: the prompt carries each message's text and comments in the order they were sent, and those rows are finished with the job (`metrics.finish_queued`). A row that joined a failed job is answered as the failed one is: the reply says to send again. A note sent while the job runs is still a request then, so it waits for the next job, with any others.
- **D3 No live steering.** Injecting a note into the reply being written would mean streaming input into `call_claude`, which every job uses, for a gain of a minute or two on a ~3-minute reply. Not planned.
- **D4 Who builds it.** D2 is in `runner/` (protected): the lead's, test-first. D1 is a developer's: `factory_dashboard/` follows F14's waiting messages already on the page.

## Before and after
- `/planning/f267`

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | waiting-notes-one-reply | L | 4 | – | D2: one job answers every waiting note on its thread |
| 02 | note-box-while-writing | D | 2 | – | D1: the box stays while the lead owes a reply |

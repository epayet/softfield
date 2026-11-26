# Milestone F308: A sent-back proposal keeps its comments in sight and takes more notes

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-26.

## Notes
When an adr is being sent back I can't see what it's being sent back with or add notes

## What happens today (from the code, 2026-11-26)
- **The comments vanish from the review page.** `factory_dashboard/templates/proposal.html` draws Comment… and its box only while the proposal is open. Once Send back is pressed the state is "on its way", so after a reload every point shows bare and the dock says only "Asked: the runner will do it." Once the runner takes it, the dock says "Sent back" and nothing more. ADR 55 on F303 waited like this for 76 minutes (sent 25 Nov 23:03, taken 00:19).
- **There's no note beside the comments.** Send back always sends `text: ""`. The runner already takes words there: `planner.sent_back` in `runner/planner.py` puts them under the comments in the lead's message. Only the page has no box for them.
- **Nothing can be added while it waits.** The review page has no box once it's on its way. The thread page does (F267, Add notes to a thread while the lead is still writing its reply), but the owner is on the review page then.

## Outcome
After a send-back, the review page keeps your words in sight: each comment under its point, your notes in the dock, dashed while on their way and solid once the lead has them, until the lead's next reply replaces the proposal. You can send a note with the comments, and add more until the lead replies. They all go into the same reply.

## Done when
- Send back on a review page with two comments and a note. After a reload, both comments show under their points and the note in the dock, all dashed.
- Add a note while it's still on its way. It shows at once under the first, and the lead's next reply answers the comments and both notes together.
- Once the runner has taken it, the same words show solid, and "Add a note" is still there until the lead replies.
- To test: send back a proposal on `/planning` with comments and a note, reload, add a note, wait for the reply. Do it on a phone too.

## Decisions
- **D1 What was sent stays on the page.** `_standing` in `factory_dashboard/thread.py` also returns the proposal's latest `send_back` since the lead's last reply (from `proposal_requests`, pending or done), read with `planner.message`. Its notes are the thread's `plan_message` requests since that reply, oldest first, leaving out the one the send-back itself became (its text starts as `planner.sent_back` writes it: `I sent back your proposal “<title>” (<id>).`). `proposal.html` draws each comment under its point as "You said". The send-back's own words and the notes go in the dock, under "Sent back <time> · N comments and a note". All of it is dashed hazard while the request waits and solid once it's done. It's drawn while the state is on its way or sent back. When the lead's next reply replaces the proposal, it goes, as the state does. Picture: [`f308-mockup/send-back.html`](f308-mockup/send-back.html).
- **D2 A note goes with Send back.** The dock gets a box, "A note for the lead, on the whole proposal", whose words go in Send back's `text`. Send back shows when there's a comment or a note, and its label says what goes ("Send 2 changes and a note back", "Send a note back"). The tab keeps the note the way deck.js keeps comments (F210 D5). Nothing in `runner/` changes: `_send_back` already passes `text` on.
- **D3 Add a note until the lead replies.** While the state is on its way or sent back, the dock has F267's plate ("Add a note") and box. It posts a `plan_message` on the card's thread, the same request as the thread page's box (`#reply` in `factory_dashboard/templates/thread.html`). The note shows at once, dashed, under what was sent. It waits for F267's ticket `f267-01-waiting-notes-one-reply`, which answers a thread's waiting messages in one reply. Without it, each note would cost its own planner reply (about $3.50).
- **D4 No edit or cancel on the review page.** A send-back waiting for the pick isn't changeable today (`_CHANGEABLE` in `runner/requests.py`), and making it so is a runner change for a gap of minutes. A later note can correct an earlier comment ("forget what I said on 2"). The notes keep F14's Edit and Cancel it on the thread page.
- **Builds on, makes removable:** builds on the existing `send_back` and `plan_message` requests, F210's tab storage and F267's note box. It adds no table, setting or job kind. Nothing becomes removable.
- **Who builds it:** all three tickets are a developer's. `factory_dashboard/thread.py` and the templates aren't protected, and `factory_dashboard/requests.py` doesn't change.

## Before and after
- `/planning/f308/proposals/plan-f308`
- `/planning/f308`

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | a-note-with-send-back | D | 2 | – | D2: a note box that goes with Send back |
| 02 | what-was-sent-back | D | 3 | 01 | D1: comments and notes stay on the review page |
| 03 | add-a-note-while-it-waits | D | 3 | 02, f267-01 | D3: Add a note in the dock until the lead replies |

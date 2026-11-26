# F308: A sent-back proposal keeps its comments in sight and takes more notes

The planning thread behind F308's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-26 07:39

> When an adr is being sent back I can't see what it's being sent back with or add notes

## The lead, 2026-11-26 07:52

> I've planned F308 as three developer tickets on the review page, with a mock-up at `.softfield/cards/f308-mockup/send-back.html`. Nothing in `runner/` changes, and the tickets pass pre-flight.
>
> 1. **Why you can't see what you sent back**: The review page only draws the comment boxes while a proposal is open. Once you press Send back, a reload shows every point bare, and the box says only "Asked: the runner will do it.". Once the runner takes it, the box says just "Sent back". Send back also always sends an empty note, and the page has no box to add one while it waits. ADR 55 on F303 waited like that for 76 minutes last night (sent 23:03, taken 00:19).
>    Action: The plan below fixes all three.
> 2. **Your comments stay under their points**: After Send back, each comment shows under its point as "You said". It is dashed while on its way and solid once the lead has it. Your note and any later notes show in the box under "Sent back 23:03 · 2 comments and a note". All of it stays until the lead's next reply replaces the proposal.
>    Action: Ticket f308-02-what-was-sent-back (developer). The mock-up shows it in moments 2 and 3.
> 3. **A note goes with Send back**: Next to the comments there will be a box, "A note for the lead, on the whole proposal". The runner already passes those words on to the lead; only the page was missing the box. You can also send back a note alone, with no comments.
>    Action: Ticket f308-01-a-note-with-send-back (developer).
> 4. **Add notes until the lead replies**: While the send-back waits, and while the lead writes, the review page has the same "Add a note" box as the thread page. Notes go on the card's thread and show at once under what you sent.
>    Action: Ticket f308-03-add-a-note-while-it-waits (developer).
> 5. **Extra notes wait for F267, Add notes to a thread while the lead is still writing its reply**: Today each note on a thread gets its own planner reply, about $3.50 each. F267's ticket f267-01-waiting-notes-one-reply (ready, the lead's) makes every waiting note go into one reply. So f308-03 waits for it, while f308-01 and f308-02 can run as soon as their turn comes. F267 sits well below F308's eventual place on the board.
>    Action: Nothing needed. If you want the note box sooner, drag F267 above F308 on the board.
> 6. **No editing or cancelling the send-back itself**: Making a waiting send-back editable means a change in the runner, for a wait that is usually minutes. A later note does the same job ("forget what I said on 2"), and notes can still be edited or cancelled on the thread page. I'd skip it.
>    Action: Nothing; say so if you want it, and I'll add a lead ticket.
>
> Proposals:
> - F308: a send-back keeps your words in sight and takes more notes (plan)
> - F308 mock-up: what a sent-back proposal was sent back with (mockup)

# F84: Coming says which reply the lead is writing, and when each other one comes

The planning thread behind F84's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:28

> Plan this card.

## The lead, 2026-10-26 23:35

> The plan, mock-up and one ticket for F84 are drafted on `plan/f84`, and the ticket passes the pre-flight check. Nothing is queued until you approve it.
>
> 1. **Why every box says the lead is writing**: I checked the code. As soon as the lead writes any reply, the dashboard tells every waiting thread that its reply is being written. It never checks which thread the reply is for. Tonight at 23:33 all 30 Coming boxes said "the lead is writing its reply now", but only this card's reply was being written; the other 29 were still in line. Each waiting thread's page said the same. The "The factory now" tile went further and said "Nothing running right now". The dashboard already has everything it needs to tell them apart: it knows which thread the running reply is for, and the lead answers the rest oldest first.
>    Action: Ticket 01 fixes this in the Planning room only.
> 2. **Only one box says "Writing now"; the others show their place in line**: The reply being written moves to the top of Coming. It gets a "Writing now" label in Opus's orange and "2 min in, about 1 min left". The next box reads "next, after F84's reply · about 1 min", then "3rd in line · about 4 min", and so on, in the order the lead takes them. Each thread's page shows its own place the same way. The times come from how long a reply usually takes, 3.3 min lately. A comment on a proposal is a message on its card's thread, so this also answers "working on a proposal": the box names the thread.
>    Action: Mock-up coming-says-which.html, built by ticket 01.
> 3. **The tile names the reply being written**: "The factory now" will read "Writing now: F84, <title> · 2 min in", with F84 linking to its thread. Under it: "Then 29 replies in line, about 1.6 h for all." Tonight that tells you how long the whole batch of cards you sent will take.
>    Action: In ticket 01.
> 4. **The thin progress bar is optional**: Under the "Writing now" box there is a thin orange bar: time spent so far against a usual reply ("2 of about 3 min"). It is the bolder version. The words already say the same thing, so you can drop it and lose nothing.
>    Action: It stays in the ticket unless you say drop it.
> 5. **Overlap with F62, Now names the card a review works on**: F62's draft names the card behind reviews and checkpoints on Now, the top bar and Next in line. The top bar's "Running: planner, job 1391" is fixed there, not here. This card only changes the lead's reply words in the Planning room. The two cards change different lines, so neither has to wait for the other.
>    Action: Nothing. Keep both cards as they are.
> 6. **A developer builds it**: One small ticket (difficulty 3) in unprotected dashboard code. It follows two examples already in the code: how the dashboard puts queued jobs in order, and how it estimates when the next reply comes.
>    Action: Ticket 01 for a developer, no dependencies.
>
> Proposals:
> - Mock-up: Coming, the tile and a thread's line say which reply is being written (mockup)
> - F84: Coming says which reply the lead is writing (plan)

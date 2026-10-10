# F90: editing seeds that i've planted but not sent to the lead…

The planning thread behind F90's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 21:45

> editing seeds that i've planted but not sent to the lead don't show the whole text. example: is the planning conversation efficient atm, in terms of…

## The lead, 2026-10-09 21:47

> I traced the bug and drafted a fix as a plan with one ticket. The fix only shows your whole note; it doesn't add a way to edit the card.
>
> 1. **Why the text is cut**: A plain Plant uses the note's first words, cut under 60 characters, as the card's title. The whole note goes into the card's doc, under Notes. The seed's page shows only that title and an empty reply box, so the rest of the note never appears there. F83 is your example: its title stops at "in terms of…" and "claude token usage?" is only in its doc. Your note is safe and the lead reads it in full; only the page hides it.
>    Action: Ticket f90-01 (the plan below).
> 2. **Show the note, don't add a way to edit it**: My suggestion: the card's page shows your whole note under the title. When a thread exists, it's folded under "Your note". To correct or add something, write it in the reply box: the lead reads the card and your message together, so it gets the change either way. Editing the card itself from the dashboard would need a new kind of request that writes to main, plus a change to the protected requests code. That's a lot of cost for nothing the reply box doesn't already do. If you really want to rewrite a seed before sending it, say so and I'll plan that instead.
>    Action: Decision D1 in F90's doc.
> 3. **The same problem is waiting in F14**: f14-02 (editing a plant while it's still in Coming) and f14-01 were written before plants became a single box. They expect a title and thoughts, but a plant now carries just its text. Built as written, the editor would likely fill in the cut title, which is this same bug again. I can't change F14's tickets from this thread.
>    Action: On F14's thread, rework f14-01 and f14-02 so they edit the plant's whole text. Say the word and I'll do it there.
> 4. **Small, so a developer builds it**: One ticket, difficulty 3. It touches only the dashboard and follows how the page already reads files from the checkout. It doesn't touch protected code or the factory's ready tickets, so you don't need to pause anything.
>    Action: Approve the plan to queue f90-01.
>
> Proposals:
> - A card's page shows your whole note (plan)

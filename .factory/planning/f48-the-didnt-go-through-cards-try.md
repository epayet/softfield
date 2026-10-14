# F48: Try again plants a note, once

The planning thread behind F48's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 08:55

> the didnt go through cards try again don't work or dismiss

## The lead, 2026-10-08 09:00

> Both buttons were doing something, but the retries were refused again, so it looked as if neither worked. I read the factory's own records (the metrics database) before answering.
>
> 1. **Dismiss worked, just late.** Six of your dismisses went through. Each one waited for the runner's next pick, 20 to 35 minutes after you pressed it.
>    *Action:* nothing for Dismiss itself.
>
> 2. **Try again was refused again, for a new reason.** Four retried notes got "is a card already". In the meantime those notes had become F35, F38 and F41, and planting refuses any note whose first six words match an existing card's. Each refusal put a new "Didn't go through" card on your desk with the same words. So a note you had just dismissed came back as a fresh card. Your words are safe: they're on F35, F38 and F41. You can dismiss the cards still showing.
>    *Action:* ticket f48-01, part 1. If the existing card already holds the note's words, nothing new is made and it says "planted already", with a link to the card. If the words are different, the note gets its own card (same name ending in "-2").
>
> 3. **One card per note.** Try again leaves the old card on the desk, so a failed retry shows two cards. Try again will now remember which card it retries. That card leaves the desk the moment you send the retry. If the retry fails too, only its new card shows.
>    *Action:* ticket f48-01, part 2. It covers both ideas and thread messages.
>
> 4. **F46 repeats this card.** F46 ("the dismiss button doesn't seem to work") is the same problem.
>    *Action:* merge F46 into F48 (proposal below).
>
> 5. **Priority 2, just after F31.** I suggest this because every retry of a planted note goes round the same loop today. It changes the card's priority from 100.
>    *Action:* set on the card. Say if you'd rather keep 100.
>
> 6. **No pause needed.** The new ticket waits in `tasks/later/` until you approve. Nothing in the queue changes.
>    *Action:* nothing.
>
> 1. **Dismiss worked, just late**: Six of your dismisses went through. Each one waited for the runner's next pick, 20 to 35 minutes after you pressed it.
>    Action: Nothing for Dismiss itself.
> 2. **Try again was refused again, for a new reason**: Four retried notes got 'is a card already'. In the meantime those notes had become F35, F38 and F41, and planting refuses any note whose first six words match an existing card's. Each refusal put a new 'Didn't go through' card on your desk with the same words, so a note you had just dismissed came back as a fresh card. Your words are safe on F35, F38 and F41; you can dismiss the cards still showing.
>    Action: Ticket f48-01, part 1: if the existing card already holds the note's words, nothing new is made and it says 'planted already', with a link to the card. If the words are different, the note gets its own card (same name ending in '-2').
> 3. **One card per note**: Try again leaves the old card on the desk, so a failed retry shows two cards. Try again will now remember which card it retries, and that card leaves the desk the moment you send the retry. If the retry fails too, only its new card shows.
>    Action: Ticket f48-01, part 2. It covers both ideas and thread messages.
> 4. **F46 repeats this card**: F46 ('the dismiss button doesn't seem to work') is the same problem.
>    Action: Merge F46 into F48.
> 5. **Priority 2, just after F31**: I suggest this because every retry of a planted note goes round the same loop today. It changes the card's priority from 100.
>    Action: Set on the card. Say if you'd rather keep 100.
> 6. **No pause needed**: The new ticket waits in tasks/later/ until you approve. Nothing in the queue changes.
>    Action: Nothing.
>
> Proposals:
> - F48: Try again plants a note, once (plan)
> - Merge F46 into F48 (merge)

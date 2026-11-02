# F196: A planted card with no tickets, and an old ADR that lost its Accept button

The planning thread behind F196's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-02 17:43

> F58 is in progress but has no tickets, can't do anything about it

## The lead, 2026-11-02 22:32

> I've traced why F58 is stuck, and there's a way to close it today. I've drafted a three-ticket plan so it doesn't happen again.
>
> 1. **Why F58, when i ask the lead a question, is stuck**: There are two faults. On 2026-10-08 you approved its merge of F57, and that approval also marked the card ready, even though it queued no tickets. So it sits under Planted with nothing to run, and Remove seed is hidden because that only shows on ideas. ADR 27 on that card also lost its Accept button: its stored path is still from before the ADRs moved out of docs/, and the page no longer reads that form. You were left with Send back and a Reject folded away. It's the only card in this state today.
>    Action: Fix both in the plan below.
> 2. **What should happen to F58 and ADR 27?**: I recommend dropping both. ADR 27 lets the lead change a priority, drop an idea or archive a thread when you ask. It came from not having an editable board, but you now drag cards on the board (F15, Reorder the board), you've said the board's order is the only order, and Archive and Remove seed are buttons on the page. What's left is typing 'put F31 first' instead of dragging it, which doesn't justify the lead writing to main without a tap. Your question on F58 was already answered on its thread. Rejecting removes the card and its notes from the current files, but its thread stays and the card remains in git history.
>    Action: Choose one. A: comment 'drop it' here, and I add that to the plan. B: press Reject on ADR 27 at /planning/f58/proposals/adr-27, which takes effect at the runner's next pick, and this card's tickets then mark ADR 27 Rejected. C: keep it, and tell me here; I'd rewrite ADR 27 for the board as it is now. If you say nothing, nothing is deleted: once the plan lands, F58 goes back to being a seed, with Accept ADR and Remove seed available.
> 3. **A simple fix for the Accept button would have accepted the wrong ADR**: F27, when i pause the factory, also has an old ADR proposal numbered 27, but its file is gone and main's ADR 27 is F58's. If the page only read the number, F27 would get an Accept button that accepts F58's ADR. So an old path now counts only when a file of exactly that name is on main, and F27's page keeps just Send back and Reject.
>    Action: Handled in f196-01 and f196-03. I'd leave F27 set aside until you come back to it; its ADR would need redrafting if you still want it.
> 4. **Where the fix sits in the queue**: Once approved, these three tickets go behind most of the 99 ready tickets, because a new card joins the back of the board. I'd leave them there: only F58 is affected today, and you can close it now with Reject. The gap they close only opens when a plan holds nothing but a mock-up or a doc.
>    Action: Nothing, unless you'd rather drag it up the board.
> 5. **No mock-up**: Nothing new is drawn. The Accept button is the one that page already has, and a card with no tickets sits in a column that already exists.
>    Action: Ask if you'd like one anyway.
>
> Proposals:
> - F196: a card is planted only with tickets, and old ADR proposals work again (plan)

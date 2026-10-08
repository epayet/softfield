# F58: when i ask the lead a question through planting an idea

The planning thread behind F58's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 12:47

> when i ask the lead a question through planting an idea
>
> can it do things, like if i ask to replan for me. or just plan? or do something and let me know what it did?

## The lead, 2026-10-08 13:10

> Short answer: today the lead can plan for you, and it can replan, but only as a draft you approve with one tap. It can't yet do something on its own and tell you afterwards. I've drafted ADR 27 to let it do small things when you ask, and I suggest merging F57 into this card.
>
> 1. **Can it plan?** Yes. On a card's thread, the lead writes the card's doc, its tickets, and any ADR or mock-up it needs. They wait as drafts until you tap Approve plan, and only then does the work go into the queue.
>    *Action:* nothing.
>
> 2. **Can it replan for you?** Yes, but not by itself. It writes the replan on the thread of the card being built, and your one tap applies it.
>    - It can only replan that card's own waiting tickets. If you ask from another thread (for example "replan F10" while on F58), it can't do it there today.
>    - I'd keep the tap. A replan changes what the line builds next, so it's worth seeing first.
>    *Action:* ADR 27 item 5. When you ask from the wrong thread, the lead says so and carries on the conversation on the right one.
>
> 3. **Can it do something and tell you what it did?** No. ADR 20 item 6 says "the lead only proposes".
>    - The one exception planned is F49: merges will happen at once.
>    - I recommend allowing a short list of small, easy-to-undo actions, only when you ask for them in so many words:
>      - **change a priority** of a card or a waiting ticket;
>      - **drop** an idea that's already done;
>      - **archive or unarchive** a thread.
>    - The dashboard already does each of these, and each is undone in one move. None of them puts work in the queue, changes code or spends Claude's time.
>    *Action:* ADR 27 (Proposed), to review below.
>
> 4. **Pushing back: why not let it do everything?** If plans, replans and ADRs were done straight from a message, a misread request could build the wrong thing for an hour before you noticed. A wrong priority costs nothing and shows at once on the thread. So I'd draw the line between tidying up (done at once) and deciding what gets built (one tap).
>    *Action:* ADR 27 item 5.
>
> 5. **How you'll see what it did:** each action shows as a "Done" line at the top of the reply, for example "F31: priority 100 → 0". If the runner refuses an action, it shows in orange with the reason.
>    - To undo, ask on the same thread ("put it back"). There's no Undo button, the same as F49's rule.
>    *Action:* ADR 27 items 3–4.
>
> 6. **F57 repeats this card.** "Reprioritise for me" is the first thing this ADR would let the lead do.
>    - I suggest keeping F58 because it's the wider question, and merging F57 into it.
>    - This goes against F49's rule of keeping the older card (flagged in the proposal).
>    *Action:* the `merge` proposal below.
>
> 7. **Tickets after the ADR.** Once you accept ADR 27, I'll write one ticket. It comes after f49-01, which builds the same "apply after the lead's reply" step.
>    *Action:* a plan on this thread after you accept.
>
> No pause is needed: nothing here touches tickets the line could start.
>
> To accept the ADR after review: `uv run runner accept 27`
>
> 1. **Can it plan?**: Yes. On a card's thread the lead writes the card's doc, tickets, ADRs and mock-ups as drafts. They go into the queue only when you tap Approve plan.
>    Action: Nothing.
> 2. **Can it replan for you?**: Yes, as a draft on the thread of the card being built, applied by your one tap. It can only replan that card's own waiting tickets, so not from another card's thread. I'd keep the tap because a replan changes what gets built next.
>    Action: ADR 27 item 5: asked from the wrong thread, the lead says so and carries on the conversation on the right one.
> 3. **Can it do something and tell you what it did?**: Not today: ADR 20 says the lead only proposes, and F49's merges are the one planned exception. I recommend letting it change a priority, drop an idea that's already done, and archive or unarchive a thread, only when you ask for it in so many words. The dashboard already does each of these, and each is undone in one move.
>    Action: ADR 27 (Proposed).
> 4. **Why not let it do everything?**: A misread plan or replan could build the wrong thing for an hour before you noticed. A wrong priority costs nothing and shows at once. So tidying up happens at once, and deciding what gets built keeps the one tap.
>    Action: ADR 27 item 5.
> 5. **How you'll see what it did**: Each action shows as a 'Done' line at the top of the reply (for example 'F31: priority 100 → 0'). A refused one shows in orange with the reason. To undo, ask on the same thread; there's no Undo button, the same as F49.
>    Action: ADR 27 items 3–4.
> 6. **F57 repeats this card**: 'Reprioritise for me' is the first thing this ADR would let the lead do. I'd keep F58 because it's the wider question, which goes against F49's rule of keeping the older card.
>    Action: Merge F57 into F58.
> 7. **Tickets after the ADR**: Once you accept ADR 27, one lead ticket follows. It comes after f49-01, which builds the same 'apply after the lead's reply' step. Nothing here touches waiting tickets, so no pause is needed.
>    Action: A plan on this thread after you accept (uv run runner accept 27).
>
> Proposals:
> - ADR 27: The lead does small things when asked, and says what it did (adr)
> - Merge F57 (reprioritise for me) into F58 (merge)

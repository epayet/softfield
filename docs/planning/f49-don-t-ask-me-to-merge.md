# F49: don't ask me to merge conversations, just do it and keep context from both in a smart way

The planning thread behind F49's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 08:55

> don't ask me to merge conversations, just do it and keep context from both in a smart way
>
> (or make a new one with information from all)

## The lead, 2026-10-08 09:03

> I've drafted a plan for F49 on `plan/f49`: the lead will merge repeat cards on its own and keep the context of both. Nothing is queued until you approve it.
>
> 1. **Merges happen without asking.** Agreed. Once the lead finds a repeat, the runner merges the two cards right after the lead's reply and commits it on main as the lead. You never see an Approve button for a merge. This goes against F6's earlier rule that a merge waits for your approval, which is why it's flagged. It's still safe: a merge only moves notes between cards and removes one, it never queues work. So "nothing is queued without your approval" still holds.
>
> 2. **A new card made from both: I advise against it.** A new card gets a new number. Links, tickets, plan branches and the card's place on the board would all move, and you'd end up with the same information. Merging into the card that's kept already holds everything.
>
> 3. **"Smart" means a summary next to your words, not instead of them.** The kept card gets the other card's notes word for word. Under them goes a short summary from the lead of what that card's thread said: what you asked, what was answered, what's still open. I won't let the lead rewrite your notes. A summary is exactly where a "smart" merge could drop what you meant, so your own words always stay beside it.
>
> 4. **Nothing from the gone card's thread is lost.** Its whole conversation is written to `docs/planning/` in the same commit. The kept card's thread gets a line: "Merged F44 here: <summary>". The lead's next answer on that thread also reads the full earlier conversation, even when it picks up a session already under way.
>
> 5. **Which card is kept.** The one further along (ready, then planning, then idea), or else the older one. Usually your new plant joins the card that already exists.
>
> 6. **The one case that still asks.** If the card being merged away has tickets, or drafts waiting on its plan branch, merging could leave them without a milestone. That stays a proposal for you, as today. It should be rare, because repeats are almost always fresh plants.
>
> 7. **Undoing a wrong merge: just say so.** I'm not proposing an Undo button. If a merge was wrong, write "split it back" on the kept thread. The lead will propose planting the card again with its notes, taken from the merge commit. If wrong merges turn out to be common, we add a button then.
>
> 8. **Order, and no pause needed.** There are two lead tickets: first the merge happening on its own, then the kept context. Both wait on F31's first ticket, `f31-01-settle-and-reject`, because they record a merge as already approved through the proposal states it adds. They're in `tasks/later/` and nothing in `tasks/ready/` changes, so you don't need to pause the factory.
>
> 1. **Merges happen without asking**: Agreed. Once the lead finds a repeat, the runner merges the two cards right after the reply and commits it on main as the lead. No Approve button. It only moves notes and removes a card, never queues work.
>    Action: Ticket f49-01
> 2. **A new card made from both: I advise against it**: A new card gets a new number, so links, tickets, plan branches and the board place all move, for the same information. Merging into the kept card holds it all.
>    Action: Nothing (D5)
> 3. **Smart means a summary next to your words**: Your notes from the other card move word for word, with the lead's short summary of its thread under them. The lead never rewrites your words.
>    Action: Ticket f49-02
> 4. **Nothing from the gone card's thread is lost**: Its thread is written to docs/planning/, the kept thread gets a line with the summary, and the lead's next answer there reads the full earlier conversation.
>    Action: Ticket f49-02
> 5. **Which card is kept**: The one further along (ready, then planning, then idea), or else the older one.
>    Action: Ticket f49-01
> 6. **The one case that still asks**: A card with tickets or drafts waiting on its plan branch stays a proposal, so its work keeps a milestone. Should be rare.
>    Action: Ticket f49-01
> 7. **Undoing a wrong merge: just say so**: No Undo button. Write 'split it back' on the kept thread and the lead proposes planting the card again from the merge commit.
>    Action: Nothing for now (D6)
> 8. **Order, and no pause needed**: Two lead tickets, after f31-01-settle-and-reject (it adds the proposal states). Both wait in tasks/later/, nothing in tasks/ready/ changes, so no pause is needed.
>    Action: Plan proposal below
>
> Proposals:
> - F49: the lead merges repeat cards itself and keeps the context of both (plan)

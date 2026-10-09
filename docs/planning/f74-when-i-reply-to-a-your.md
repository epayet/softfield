# F74: when i reply to a 'your answers wanted' thread, there's a…

The planning thread behind F74's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 19:10

> when i reply to a 'your answers wanted' thread, there's a duplicated box in 'coming' of the same thing, and the original box is still in your desk and not orange dotted. the 'coming' part should just have 'coming plants' (or seeds?), while if i answered on a thread it should stay there as orangely dotted if waiting to be picked up the same way with proposals atm

## The lead, 2026-10-09 19:12

> I've drafted a plan for F74: one developer ticket that fixes the duplicate box. Coming will hold only plants, and a thread you've replied on keeps a single dashed orange box in "Your answers wanted" until the lead's reply arrives.
>
> 1. **Why you see two boxes**: Your message only reaches the thread when the runner picks it up. Until then the desk still thinks the lead spoke last, so the box stays solid in "Your answers wanted". Coming separately lists any thread with a message on its way, so the same thread shows twice. The code that dashes a box (it handles Archive, Sign off and Remove seed) doesn't know about messages. After the pick it gets worse: the thread drops out of "Your answers wanted" and only Coming shows it, until the lead replies and it jumps back.
>    Action: Ticket f74-01 (point 2).
> 2. **One box per conversation, in "Your answers wanted"**: As you asked: once you send a message, the thread's box stays where it was, dashed orange, saying when the reply comes ("waiting for the lead · after f63-01, ~12 min", or the Claude limit when the job is held). A dashed box no longer counts as waiting for you, the same as proposals today.
>    Action: Ticket f74-01 (developer, difficulty 3).
> 3. **Dashed until the lead replies, not only until the pick**: You wrote "waiting to be picked up". If the dashing stopped at the runner's pick, the box would vanish for however long the lead takes to write, sometimes most of an hour. I recommend it stays dashed until the lead's reply is stored, then turns solid. Alternatives: (a) until the lead replies (recommended); (b) until the pick only, after which the thread disappears from the desk until the reply.
>    Action: Plan D3; choose (a) or (b).
> 4. **What Coming is called**: Coming will show only plants that haven't been picked up yet. I recommend "Coming seeds": "seed" is already the desk's word for an idea card ("Seeds, not asked about yet"), and that's what a plant becomes. Alternatives: (a) "Coming seeds" (recommended); (b) "Coming plants"; (c) keep "Coming".
>    Action: Plan D1; choose a name.
> 5. **A first message on a seed, or on an archived thread**: These had no box in "Your answers wanted", so Coming was the only place they showed. They will now appear there as a dashed box straight away, and the seed leaves "Seeds, not asked about yet" so it shows once. "Plant and ask the lead" shows in Coming seeds until the pick, then becomes a dashed conversation: it moves once, because by then it really is a card with a thread.
>    Action: Plan D2 and D4, in f74-01.
> 6. **Runs after F63's reorder, alongside F14**: This isn't a repeat of another card. F63's ticket (ready) reorders the same desk groups and moves Coming in the same template, so f74-01 waits for it. F63's notes describe Coming as also holding "a message waiting for the lead"; F74 overrides that line, but F63's ticket doesn't change it, so nothing needs a replan. F14's f14-02 (edit or cancel a plant in Coming) works on the plant rows, which F74 leaves alone.
>    Action: Nothing; f74-01 depends on f63-01.
>
> Proposals:
> - F74: one box per conversation, Coming for plants only (plan)

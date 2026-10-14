# F41: I find that on conversations, there is the raw text and then small boxes to review each point. the information is not…

The planning thread behind F41's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 08:20

> I find that on conversations, there is the raw text and then small boxes to review each point. the information is not…
>
> I find that on conversations, there is the raw text and then small boxes to review each point. the information is not exactly the same and the most interesting part are the boxes so i tend to just scroll down and ignore the raw text
>
> how relevant is the raw text, and perhaps it should be hidden until i want to see it? like an accordion. focus is on the boxes and the decisions. This was on deskrop

## The lead, 2026-10-08 08:22

> I've drafted the plan for F41. The duplicated text isn't the dashboard's fault: the prompt asks me to write the points twice. Nothing is queued until you approve.
>
> 1. **How useful is the text above the boxes? Hardly at all.** The prompt asks me for "numbered points" in the reply, then asks for the same points again in the block the boxes are built from. So I write everything twice, once as prose and once as boxes, and the two drift apart. That's why they don't say quite the same thing. Your comments attach to the boxes, and the next round reads the boxes, so the boxes are the real record.
>    → Ticket f41-01, which I do myself: the prompt will say that everything goes in the points and that the text above them is two short lines at most, or nothing.
>
> 2. **Fold the text, but fix the cause too.** On its own, a fold would hide a second copy that can disagree with the boxes. If something mattered only in the hidden text, like a request to pause the factory, you'd miss it. So we do both: the prompt change stops the doubling, and the fold tidies the older replies and any that still drift.
>    → Ticket f41-02 for a developer: a reply that has boxes shows its text in a closed "Full reply" fold above them, on desktop and phone.
>
> 3. **Never fold a reply that has no boxes.** When a reply's block of points is broken, the text is all there is. It ends with a note saying why the points weren't read, and that has to stay in sight. Your own messages never fold either.
>    → Part of f41-02.
>
> 4. **F44 belongs in this card.** F44 is about the "no duplicate" box that tells you nothing. It isn't a repeat of F41, but it's the same problem (my replies make you read things you can't act on), and it's fixed in the same lines of the same prompt. So f41-01 also says that no box may report that nothing was found. I'd merge F44 in so one ticket closes both. This reply already works that way: no "no duplicate" box.
>    → A merge of F44 into F41.
>
> 5. **Not touched.** The proposal page stays as it is, along with the boxes, their comment fields and the one-at-a-time view on the phone. The history the next planning job reads still keeps the full text. F30 (newest answer first) and F42 (the small scroll area on proposals) concern the same pages but are separate cards.
>    → Nothing.
>
> The plan is in `docs/milestones/f41-i-find-that-on-conversations-there.md`, and the two tickets are in `tasks/later/`. The factory doesn't need pausing, since neither ticket is queued yet.
>
> 1. **How useful is the text above the boxes? Hardly at all**: The prompt asks for numbered points in the reply and again in the block the boxes come from, so I write everything twice and the copies drift apart. The boxes are the record: your comments and the next round use them.
>    Action: Ticket f41-01 (mine, the runner's code is protected): everything goes in the points, the text is two short lines at most.
> 2. **Fold the text, but fix the cause too**: A fold alone hides a second copy that can disagree with the boxes, so you could miss something, like a request to pause. The prompt change stops the doubling; the fold tidies older replies and any that still drift.
>    Action: Ticket f41-02 (developer): a reply with boxes shows its text in a closed 'Full reply' fold above them, on desktop and phone.
> 3. **Never fold a reply that has no boxes**: When the block of points is broken, the text is all there is, and its note saying why must stay in sight. Your own messages never fold.
>    Action: Part of f41-02.
> 4. **F44 belongs in this card**: Not a repeat of F41, but the same problem (things in my replies you can't act on), fixed in the same prompt lines. f41-01 also forbids boxes that only say nothing was found.
>    Action: Merge F44 into F41.
> 5. **Not touched**: The proposal page, the boxes and their comments, the one-at-a-time phone view, and the history the next job reads all stay as they are. F30 and F42 are on the same pages but are separate cards.
>    Action: Nothing.
>
> Proposals:
> - F41: say it once, in the points, and fold the rest (plan)
> - Merge F44 (no 'nothing found' points) into F41 (merge)

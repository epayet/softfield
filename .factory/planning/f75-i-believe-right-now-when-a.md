# F75: I believe right now, when a plan gets approved or…

The planning thread behind F75's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 20:34

> I believe right now, when a plan gets approved or rejected, it archives the conversation thread that goes with it. currently if i approve or reject a proposal and that it's on its way, the proposal is displaying 'on its way' with the orangely dotted line which is great. assuming this action will archive the thread as well, currently it doesn't look like the thread will be archived. i want it to be displayed as much as well, so that i know that this thread will soon be archived too

## The lead, 2026-10-09 20:36

> You're right: approving or rejecting does archive the thread (since f31-01). Only the thread's box doesn't show it yet. I've drafted the plan as one small developer ticket.
>
> 1. **You're right: approving or rejecting archives the thread**: Since f31-01, once every proposal in the lead's latest reply is approved or rejected, the runner adds a line ('Approved by the owner on …') and archives the thread. It does this only when it applies your approval at its next pick. Until then only the proposal is dashed orange. The thread's box in 'Your answers wanted' stays solid and still counts as waiting for you, because the dashed look is only wired up for a manual Archive, Sign off or Remove seed.
>    Action: Ticket f75-01 (point 2).
> 2. **The thread's box goes dashed at the same moment as the proposal**: When your Approve or Reject settles the last open proposal of the reply, the thread's box turns dashed orange and says 'archiving at the runner's next pick', the same words a manual Archive uses. It stops counting as waiting for you. The thread's own page shows the same 'Archiving at the runner's next pick' mark.
>    Action: Ticket f75-01, developer, difficulty 3.
> 3. **Only when the thread will really be archived**: If the reply proposed a plan and an ADR and you approve only the plan, the runner won't archive the thread, so its box stays solid. Showing 'archiving' there would be wrong. One exception: rejecting a plan drops every draft on its branch, the ADR too. So a pending reject counts for all of that reply's drafts, and the box goes dashed at once.
>    Action: Milestone doc decisions D1 and D2.
> 4. **If the runner refuses your approval, the box goes back to normal**: If the runner refuses your approval, the proposal is open again, and the thread's box goes solid and counts again on the next refresh. Nothing extra to build.
>    Action: Nothing.
> 5. **It waits for F74 and F22**: F74, one box per conversation (ready), rewrites the same 'Your answers wanted' boxes and their dashed look. F22, the archive button at the bottom (ready), moves the thread page's archive mark. f75-01 goes after both so the three don't clash. It's a different problem from F74 (your message on its way vs. your approval on its way), so it's not a repeat.
>    Action: f75-01 depends on f74-01 and f22-01.
>
> Proposals:
> - F75, the thread shows it's being archived once you approve or reject (plan)

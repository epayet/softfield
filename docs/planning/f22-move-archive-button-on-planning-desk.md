# F22: move archive button on planning desk at the bottom rather than the top

The planning thread behind F22's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-07 23:08

> move archive button on planning desk at the bottom rather than the top

## The lead, 2026-10-07 23:11

> I've drafted a plan for F22 and one small ticket on `plan/f22`. Nothing is queued until you approve it.
>
> 1. **Is it a repeat?** No. None of the idea, planning or ready cards, and none of the other threads (F11 to F29), are about where the Archive button sits. F23 and F24 are also about the thread page, but they cover comments and answers. → Nothing to merge.
>
> 2. **Where it is now and where it goes.** The Archive (or Unarchive) button is in the card's header at the top of each `/planning/<card>` thread (`factory_dashboard/templates/thread.html:26-42`). I'm moving it below the reply box, where you are once you've read the thread to the end. → Ticket `f22-01-archive-at-the-bottom`.
>
> 3. **A catch on the phone.** On a phone the Send box stays pinned to the bottom of the screen while you scroll the thread. If Archive went inside the thread, it would sit hidden under Send. So it goes just after the thread instead: Send stays pinned while you read, and Archive shows once you scroll past the end. → Written into the ticket.
>
> 4. **I suggest moving "Remove seed" too.** A seed's header also has "Remove seed". Like Archive, it ends a card. If only Archive moves, the top still has a button that ends a card, and the two would be in different places. I recommend moving both into one row at the bottom. The alternative is to move Archive only. → Done in the plan and the ticket; comment if you'd rather keep "Remove seed" at the top.
>
> 5. **Nothing else changes.** When you tap Archive, it still shows at once with a dashed orange edge and the button goes. The runner archives the thread at its next pick, and a reply still opens the thread again. → Nothing to do.
>
> 6. **Who builds it.** It's a small template change with no protected files, so a developer gets it at difficulty 2. The existing tests find the button by its name on the page, so they don't depend on where it sits. The ticket adds a test that it comes after the reply box. → Ticket, developer.
>
> 7. **No need to pause the factory.** This is a new ticket in the "later" folder and it doesn't change any F22 ticket waiting in the queue, so the line can't start it while we talk. → Nothing to do.
>
> 1. **Is it a repeat?**: No. None of the idea, planning or ready cards, and none of the other threads (F11 to F29), are about where the Archive button sits. F23 and F24 are also about the thread page, but they cover comments and answers.
>    Action: Nothing to merge.
> 2. **Where it is now and where it goes**: The Archive (or Unarchive) button is in the card's header at the top of each thread page. I'm moving it below the reply box, where you are once you've read the thread to the end.
>    Action: Ticket f22-01-archive-at-the-bottom.
> 3. **A catch on the phone**: On a phone the Send box stays pinned to the bottom of the screen while you scroll the thread. If Archive went inside the thread, it would sit hidden under Send. So it goes just after the thread instead: Send stays pinned while you read, and Archive shows once you scroll past the end.
>    Action: Written into the ticket.
> 4. **I suggest moving "Remove seed" too**: A seed's header also has "Remove seed". Like Archive, it ends a card. If only Archive moves, the top still has a button that ends a card, and the two would be in different places. I recommend moving both into one row at the bottom. The alternative is to move Archive only.
>    Action: Done in the plan and the ticket; comment if you'd rather keep "Remove seed" at the top.
> 5. **Nothing else changes**: When you tap Archive, it still shows at once with a dashed orange edge and the button goes. The runner archives the thread at its next pick, and a reply still opens the thread again.
>    Action: Nothing to do.
> 6. **Who builds it**: It's a small template change with no protected files, so a developer gets it at difficulty 2. The existing tests find the button by its name on the page, so they don't depend on where it sits. The ticket adds a test that it comes after the reply box.
>    Action: Ticket, developer.
> 7. **No need to pause the factory**: This is a new ticket in the "later" folder and it doesn't change any F22 ticket waiting in the queue, so the line can't start it while we talk.
>    Action: Nothing to do.
>
> Proposals:
> - F22: Archive and Remove seed at the bottom of a thread (plan)

## The owner, 2026-10-07 23:18

> go

## The lead, 2026-10-07 23:34

> I've taken your "go" as agreeing to every point. The plan is ready for you to approve from the dashboard. Nothing is queued until you approve it there.
>
> 1. **Agreed as drafted.** All seven points from my last reply stand. Archive and "Remove seed" move together into one row at the bottom of the page, just after the thread and the reply box. → Approve "F22: Archive and Remove seed at the bottom of a thread" on the dashboard. That queues `f22-01-archive-at-the-bottom` for a developer.
>
> 2. **Not a repeat, but it overlaps with F30.** F31 (the Approve plan button looks like you can keep clicking it) is a different button, so I'm not proposing a merge. F30 (newest answer first, so you don't have to scroll) changes the order of the thread on the same page. If F30 puts the newest message at the top, "after the thread" would mean below the oldest message. I recommend building F22 now, since it's one small ticket. When we plan F30, Archive stays at the very bottom of the page and F30 updates F22's test. → Added to the F22 plan as D3; I'll raise it again when we plan F30.
>
> 3. **No need to pause the factory.** The ticket stays in the "later" folder until you approve, and no F22 ticket is waiting in the queue. → Nothing to do.
>
> 1. **Agreed as drafted**: All seven points from my last reply stand. Archive and "Remove seed" move together into one row at the bottom of the page, just after the thread and the reply box.
>    Action: Approve "F22: Archive and Remove seed at the bottom of a thread" on the dashboard. That queues f22-01-archive-at-the-bottom for a developer.
> 2. **Not a repeat, but it overlaps with F30**: F31 (the Approve plan button looks like you can keep clicking it) is a different button, so I'm not proposing a merge. F30 (newest answer first, so you don't have to scroll) changes the order of the thread on the same page. If F30 puts the newest message at the top, "after the thread" would mean below the oldest message. I recommend building F22 now, since it's one small ticket. When we plan F30, Archive stays at the very bottom of the page and F30 updates F22's test.
>    Action: Added to the F22 plan as D3; I'll raise it again when we plan F30.
> 3. **No need to pause the factory**: The ticket stays in the "later" folder until you approve, and no F22 ticket is waiting in the queue.
>    Action: Nothing to do.
>
> Proposals:
> - F22: Archive and Remove seed at the bottom of a thread (plan)

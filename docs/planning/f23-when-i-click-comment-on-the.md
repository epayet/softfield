# F23: when i click comment on the planning desk ticket, i want it to focus on the text box

The planning thread behind F23's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-07 23:08

> when i click comment on the planning desk ticket, i want it to focus on the text box
>
> i currently need to click on both comment and then cilkc on the box to start typing

## The lead, 2026-10-07 23:12

> 1. **Not a repeat.** I read every idea, planning and ready card and the open threads. The closest is F22, which moves the Archive button on the same desk. That's a different change, so nothing to merge. Action: nothing.
>
> 2. **Why you tap twice.** Each point's "Comment…" on a planning thread (`/planning/f23`) opens a box, but nothing puts the cursor in it. The review page (Accept / Send back) already does this, so only the thread page needs fixing. Action: the ticket in point 4.
>
> 3. **A catch on the phone.** The obvious fix ("put the cursor in the box once it has opened") works on a computer, but on an iPhone the keyboard wouldn't come up. iPhones only show it if the cursor moves during the tap itself. So the plan opens the box and moves the cursor in the same tap. A second tap still closes it and keeps your text. Action: written into the ticket.
>
> 4. **One small developer ticket.** It's `f23-01-comment-focus` (difficulty 2), with the review page's working code as its example. How to test: open a thread with points, tap "Comment…" on point 2 and type straight away, on the computer and on your phone. Action: approve the plan to queue it.
>
> 1. **Not a repeat**: No card or thread asks for this. F22 (move Archive) is on the same desk but a different change.
>    Action: Nothing
> 2. **Why you tap twice**: The thread page's Comment… opens the box but nothing puts the cursor in it. The review page already does this; only the thread page needs fixing.
>    Action: The ticket in point 4
> 3. **A catch on the phone**: Putting the cursor in after the box opens wouldn't bring up the iPhone keyboard. The fix opens the box and moves the cursor in the same tap; a second tap still closes it and keeps your text.
>    Action: Written into the ticket
> 4. **One small developer ticket**: f23-01-comment-focus, difficulty 2, following the review page's example. Test: tap Comment… on a point and type straight away, on the computer and on the phone.
>    Action: Approve the plan to queue it
>
> Proposals:
> - F23: Comment… puts the cursor in its box (plan)

## The owner, 2026-10-07 23:22

> agreed

## The lead, 2026-10-07 23:34

> 1. **Agreed, so the plan is ready to approve.** The draft on `plan/f23` hasn't changed: the card's plan and one ticket, `f23-01-comment-focus`. Replying "agreed" doesn't queue it, though. Action: press **Approve plan** on F23's plan in the planning room. The runner then merges the draft and queues the ticket.
>
> 2. **Still not a repeat, including the two new cards.** F30 (latest answer first) and F31 (Approve plan looks like it can be clicked again) are different changes. F30 will also edit the same page (`thread.html`). F23's change is small and separate from F30's, so whichever lands second just builds on the first. Action: nothing.
>
> 1. **Agreed, so the plan is ready to approve**: The plan and its one ticket (f23-01-comment-focus) haven't changed. Replying 'agreed' doesn't queue them.
>    Action: Press Approve plan on F23's plan in the planning room
> 2. **Still not a repeat, including F30 and F31**: F30 (latest answer first) and F31 (Approve plan clickable again) are different changes. F30 also edits thread.html, but its change is separate from F23's.
>    Action: Nothing
>
> Proposals:
> - F23: Comment… puts the cursor in its box (plan)

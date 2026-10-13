# F106: where do blocked tickets go for me to review

The planning thread behind F106's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-12 21:02

> where do blocked tickets go for me to review

## The lead, 2026-10-12 21:04

> Answered from the code, and drafted F106's card as a plan outline (decisions only, no tickets written yet).
>
> 1. **Where blocked tickets go today**: Nowhere you'd look. The runner moves the ticket to the folder tasks/blocked/ with its reason, keeps the work on the branch task/<ticket>, and pauses the tickets that depend on it. On the dashboard they show only in the Overview's "while you were away" line (a link per blocked ticket) and on /tickets if you type "blocked" in the State box. Your desk on /planning has no group for them.
>    Action: F106's card now holds a draft plan to put them on your desk (the proposal below).
> 2. **"Needs you" misses them while the runner runs on its own**: A blocked ticket becomes a "Needs you" item only when the runner writes a milestone's verdict: at the end of `runner milestone`, or after a review under `runner run`. Blocking itself stores nothing, so with the standing `runner run` a blocked ticket can sit unseen. I read this from the code; I couldn't query the database from this job to confirm that none of the four below has an open item.
>    Action: Ticket 01 of the draft: the runner stores the item the moment it blocks a ticket.
> 3. **Nothing brings a blocked ticket back**: No command or button moves a ticket out of tasks/blocked/. The command the item shows (`uv run runner milestone <key>`) reruns the milestone and skips the blocked ticket again; `runner queue` only takes tickets that were set aside.
>    Action: Ticket 03 of the draft: "Try again" and "Set aside" buttons on the desk item.
> 4. **Four tickets are blocked right now**: All four are the lead's own tickets: f21-01-planner-sees-the-plan, f21-02-sections-in-prompts and f31-03-point-outcomes (the checks failed, the work is kept on their branches) and f21-03-trim-owner (the lead job changed nothing). Three of F21's tickets are stuck, so F21 isn't moving. I can't touch another milestone's tickets from this thread.
>    Action: A terminal session, with the runner stopped: `claude --model opus "Unblock f21-01, f21-02, f21-03 and f31-03: read each branch and its logs, finish or rewrite each, and put them back in tasks/ready/"`. Or wait for F106 and do it from the desk.
> 5. **You shouldn't review blocked tickets yourself**: I disagree with "for me to review" as the goal. A blocked ticket is a failed piece of work, and reading its branch and logs is the lead's job, not yours. I recommend that the runner asks the lead to look first, on the card's thread, so what reaches your desk is a suggested fix to approve (the ticket reworked, split or set aside), with "Try again" and "Set aside" beside it. The cost: one Opus planner job per blocked ticket, and it changes a workflow rule, so it needs an ADR. The cheaper alternative is the two buttons alone, and you ask the lead on the thread when you want.
>    Action: Your choice: the lead looks first (I recommend it, and I draft the ADR next turn), or the buttons only.
> 6. **No mock-up planned**: This adds one group to the desk you already have, in the same shape as "Didn't go through", so I'd skip the mock-up and write the tickets once you agree with the decisions.
>    Action: Nothing, unless you want a mock-up first.
>
> Proposals:
> - F106: blocked tickets reach your desk, with a fix to approve (plan)

## The owner, 2026-10-12 21:33

> I sent back your proposal “F106: blocked tickets reach your desk, with a fix to approve” (f106-plan).
> - On its key point 5 (Four tickets, written after you agree): why no tickets yet?

## The lead, 2026-10-12 21:36

> The five tickets and the ADR are now drafted on `plan/f106`. I could not run the pre-flight dry run from this job, so the tickets are checked by hand only (every path and function they name exists).
>
> 1. **Why there were no tickets**: I was holding them back for your choice between "the lead looks first" and "buttons only". That was the wrong call: three of the tickets are the same either way and could have been written at once. They are all written now.
>    Action: Nothing: the plan below carries the five tickets.
> 2. **I took "the lead looks first" as agreed**: You didn't comment on that choice, so I drafted ADR 29 for it. If you'd rather have the buttons only, reject the ADR and tickets 04 and 05 go with it; tickets 01 to 03 stand alone.
>    Action: Accept ADR 29, or reject it to keep the buttons only.
> 3. **"Try again" on a lead ticket starts from scratch**: I was wrong last time to say the branch is kept. From the code, a lead ticket's branch is reset to main when it runs again, so its failed work would be wiped. Ticket 01 has the runner copy that work to a branch named blocked/<ticket> before the retry.
>    Action: Ticket 01 covers it.
> 4. **A replan can't touch a blocked ticket today**: The lead's fix only helps if it can bring the blocked ticket back, and a replan currently reaches only the waiting tickets of its card. That added a fifth ticket and an item in the ADR.
>    Action: Ticket 05 and ADR 29 item 3.
> 5. **Blocked tickets show once on the Overview**: The Overview will count them through the "things wait on your desk" line, not as rows of their own too. This is the same fix F95 makes for sign-offs, so the two numbers can't disagree.
>    Action: Ticket 02, which waits for F95's first ticket.
> 6. **The developer tickets wait for two others**: Ticket 02 waits for f12-03 (it removes a stray test file that makes every developer ticket fail the checks) and f95-01. Both are in the queue already. Nothing of F106 can be seen on the desk before they merge.
>    Action: Nothing, unless you want f12-03 moved up the queue: it holds up every developer ticket, not only these.
> 7. **The four blocked tickets still wait**: F106 won't unblock f21-01, f21-02, f21-03 and f31-03 by itself: once ticket 01 is in, they show on your desk with Try again, but the lead's look only fires for tickets blocked after ticket 04.
>    Action: A terminal session with the runner stopped: `claude --model opus "Unblock f21-01, f21-02, f21-03 and f31-03: read each branch and its logs, finish or rewrite each, and put them back in tasks/ready/"`.
>
> Proposals:
> - ADR 29: The lead looks at a blocked ticket before you do (adr)
> - F106: blocked tickets reach your desk, with a fix to approve (plan)

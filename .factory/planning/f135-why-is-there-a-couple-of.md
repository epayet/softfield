# F135: Reviews stop at once: they look for end-to-end tests the split removed

The planning thread behind F135's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-15 08:37

> Why is there a couple of 'end-to-end tests fail on staging
> softfield milestone f28-the-first-time-i-clicked-on' review stop on the overview

## The lead, 2026-10-15 08:40

> Both stops on the Overview come from the same bug, and no test actually failed. Since ADR 30 split Coucou out, Softfield's milestone reviews still try to run Coucou's end-to-end tests, which are no longer in this repo. I've drafted one lead ticket on plan/f135 that fixes it.
>
> 1. **Why the two stops are there**: Before each review round, the runner runs the end-to-end tests in tests/e2e. Those were Coucou's browser tests, and they left with the split on 2026-10-14 (ADR 30). So the run finds no folder ('file or directory not found: tests/e2e'), runs no test, and the runner records it as 'end-to-end tests fail on staging'. F28, 'The first time I clicked on…', and F19, 'Will I need to refresh planning…', are the first two reviews since the split, and both stopped before Claude read a line. F26's review on 2026-10-10 was the last clean one. Neither milestone is broken: neither has had a review yet. The wording 'on staging' is wrong too, because there is no staging.
>    Action: Fix it with the ticket in point 2.
> 2. **The fix: no end-to-end tests, no end-to-end run**: One lead ticket, because the runner's code is protected. A project with no tests/e2e folder skips that run and goes straight to Claude's review rounds. Coucou keeps its run as it is. A review that was stopped this way becomes due again, so F28 and F19 get their real review without you doing anything. I chose not to add a setting for it, because no project needs one yet. It goes first among your priority-1 work and takes about one ticket's time.
>    Action: Approve the plan to queue f135-01-no-e2e-no-stop.
> 3. **The two items leave Needs you on their own**: Once F28's and F19's reviews run again, their new verdict takes the old stop items off Needs you. Until the fix merges, they stay, and the only other way to clear them is a terminal command you don't need to run. F101, 'uv runner run command stopped when…', is next to be reviewed and would get the same stop if it runs before the fix.
>    Action: Nothing for you to do.
> 4. **No mock-up**: Nothing on a page changes. The fix only stops false items from appearing.
>    Action: Nothing.
>
> Proposals:
> - F135: reviews skip the end-to-end run when a project has none (plan)

## The owner, 2026-10-15 09:07

> how about this, is this related: [08:40:53] ▶ [runner] e2e tests
> [08:40:53] ■ [runner] e2e tests failed · 0 min
> [08:40:54] [runner] Nothing to do.
>
> ⚠ NEEDS YOU
>   • review stopped: end-to-end tests fail on staging

## The lead, 2026-10-15 09:08

> Yes, it's the same bug. The plan already drafted fixes it, so nothing changes in it.
>
> 1. **Yes: that's F101's review hitting the same stop**: The log you pasted is from F101's review ('uv runner run command stopped when…') at 08:40. It was the third case I mentioned last time. It's the same cause: before its first round, the review looks for Coucou's tests/e2e folder, which left with the split. No test runs, so it says 'failed' after 0 minutes and stops. 'Nothing to do' only means the queue had nothing else to run after that.
>    Action: No new work: the ticket in the plan, f135-01-no-e2e-no-stop, fixes this case too.
> 2. **F101 was signed off without Claude's review**: You signed F101 off at 09:08, and its stop item went with the sign-off. That means no Claude review round ever read F101's two tickets; only the checkpoints did. I wouldn't reopen it, because it was small and you tested it yourself. F28 ('The first time I clicked on…') and F19 ('Will I need to refresh planning…') are different: they still wait in Needs you, and the fix will review them on its own.
>    Action: Nothing for F101. Until the fix merges, every new review will stop the same way. Approving the plan on this page queues the fix first among priority-1 work, and it waits for no other ticket.

## The owner, 2026-10-15 11:37

> plan says replaced by newer reply. approve the plan for me, or update it if you can't

## The lead, 2026-10-15 11:37

> I can't approve it for you: only your Approve on this page queues work. My last reply sent an empty list, and that took the plan's button away. That was my mistake. The plan is listed again below with no changes, so its Approve button is back. I also noted F101 in the card's facts.
>
> 1. **The plan is back: press Approve on it**: I can't approve a plan myself: the runner queues work only when you press Approve. The plan said 'replaced by newer reply' because my last reply sent an empty list, which took the plan's button away. That was my error. The plan is listed again below, unchanged apart from one added fact on the card: F101 ('uv runner run command stopped when…') hit the same stop at 08:40 and was signed off without a review. The ticket still passes the checks.
>    Action: Press Approve on 'F135: reviews skip the end-to-end run when a project has none'. That queues f135-01-no-e2e-no-stop at priority 1, waiting for no other ticket. Once it merges, F28 ('The first time I clicked on…') and F19 ('Will I need to refresh planning…') get their reviews and leave Needs you.
>
> Proposals:
> - F135: reviews skip the end-to-end run when a project has none (plan)

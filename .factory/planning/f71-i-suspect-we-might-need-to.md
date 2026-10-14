# F71: I suspect we might need to increase the timeouts as the…

The planning thread behind F71's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 08:46

> I suspect we might need to increase the timeouts as the tests take quite some time. i see dev tasks that are taking almost 45 minutes to complete, but do manage to complete, what would be a good value

## The lead, 2026-10-09 08:51

> I recommend 60 minutes. The cut-off is already 45 minutes, so the attempts you're seeing finish just under it. I've put this on the F71 card and drafted a one-line ticket for the lead (a plan you approve).
>
> 1. **The cut-off is already 45 minutes**: A developer attempt is stopped after 2700 s (45 min), set in M4 after 8 of m4-06's 9 attempts hit the old 30-minute limit. So the attempts you saw at almost 45 minutes only just made it. One slightly bigger ticket would be cut off with its work half done. You're right that the limit is now tight.
>    Action: Plan F71, ticket f71-01.
> 2. **A good value: 60 minutes, not more**: Set the developer attempt limit to 3600 s. That gives tickets that now finish in 40–45 min about 15 minutes more room. I'd stop at 60: most timeouts in recent session reports were attempts that were going nowhere (F6's page tickets, f8-06's third attempt). A longer limit doesn't save those. It only holds the GPU longer. A ticket that fails three times would then use 3 hours instead of 2 h 15. Stuck attempts are still stopped after 10 minutes with no edit, so the extra time goes to attempts that are working.
>    Action: Ticket f71-01 (lead, difficulty 1): opencode = 3600 in workflow/runner.toml.
> 3. **The other limits stay as they are**: The full test run (check-all) takes 5–10 minutes. Its gate limit (15 min) and the developer's shell limit (15 min) both cover that. Claude's jobs (30 min) and milestone reviews (60 min) aren't hitting their limits.
>    Action: Nothing.
> 4. **Speeding up the tests helps more than a longer limit**: A developer runs check-all at least once and often two or three times, at 5–10 minutes each. That's a third or more of each attempt. Making check-all faster would shorten every ticket, while a longer limit only saves the few that run close to it. F4 left 'why is check-all slow' for later. Before planning it, I'd like a week of real numbers.
>    Action: F71 D3: after a week, read the jobs table for attempts that passed after 45 min and attempts that timed out at 60. If timeouts still end without a merge, go back to 45. If tests take most of the time, plant a card to make check-all faster.
> 5. **Why it's a lead ticket and not a direct edit**: workflow/ is protected, so a developer can't change it, and from the planning room I can only draft. The lead's job is a single line, and the attempt limit doesn't apply to it. You can also make the change yourself; config limits don't need an ADR.
>    Action: Approve the F71 plan, which queues f71-01.
>
> Proposals:
> - F71: give developer attempts 60 minutes (plan)

## The owner, 2026-10-09 20:34

> make a separate investigation on the slow tests and suggested steps. they still need to be quite thorough for the less capable developers but they seem like a big bottleneck atm
>
> On point 3: is'nt claude also getting close to the limit with the currently long and getting longer tests?

## The lead, 2026-10-09 20:38

> Yes, Claude's jobs are getting close to their limit too, so I've added that to f71-01. The slow-tests investigation is a new ticket, f71-02, and approving the plan queues both.
>
> 1. **Yes, Claude's jobs are getting close to their limit too**: Lead tickets, escalations that take over a ticket, directions and checkpoints all get the same 30 minutes. Each runs the full test run (check-all) once or twice, which is 10–20 of those 30 minutes. No session report shows a Claude job cut off yet, but the margin shrinks as the tests grow. When a Claude job is cut off, everything it already spent is lost, which costs more than waiting. Giving it more time costs nothing unless a job needs it. I can't see the exact Claude job times from the planning room: they're in the metrics database, which I can't read from here. f71-02 will measure them.
>    Action: f71-01 now also raises Claude's limit from 30 to 45 minutes (F71 D2). Milestone reviews stay at 60.
> 2. **The investigation: same tests, run better**: Here's what I found from the code before measuring. One ticket runs the whole suite four or five times: the developer's check-all two or three times, the all-tests gate on the same files, the 'tests fail without the change' check, then check-all again at merge. Every run is one test after another, with nothing in parallel, browser tests included. So the biggest savings may come from running in parallel and not repeating a run that just passed. Neither removes a test. The study measures first, then gives each step a verdict with minutes saved per ticket.
>    Action: Ticket f71-02-slow-tests-study (lead, difficulty 4). It writes a Findings section on this card, tickets in tasks/later/ and, for a gate change, a draft ADR. It changes nothing itself.
> 3. **Running tests in parallel has a cost**: Parallel tests would use every CPU core on the same machine where Qwen runs, and that machine already reaches about 90 °C. Browser tests and the live test server may also clash when they run side by side. The study checks both before it recommends anything.
>    Action: Part of f71-02's verdict on running in parallel.
> 4. **The investigation sits on this card, not a new one**: You asked for it separately. It is its own ticket, but on F71 rather than a new card. From a card's thread I can't plant a new card with an approve button: that only works on the general thread. Keeping it here means one approval queues both tickets, and the topic is the same. If you'd rather have it as its own card, plant it and I'll move the ticket over.
>    Action: Nothing, unless you plant a card.
> 5. **f71-02 runs after the new limits**: Measuring the suite means running it several times. That could take a 30-minute Claude job past its limit, so f71-02 waits for f71-01.
>    Action: f71-02 depends on f71-01.
>
> Proposals:
> - F71: longer limits, then a study of the slow tests (plan)

## The owner, 2026-10-10 19:10

> I sent back your proposal “F71: longer limits, then a study of the slow tests” (f71-plan).
> - On its key point 4 (D4: look again after a week): Don't look again. Just for a report now and suggest immediate follow ups for me to approve. I have a separate task to do periodic reviews of the factory

## The lead, 2026-10-10 19:13

> Done: the later look is gone, and the report now covers it.
>
> 1. **No later look: the report answers it now**: Agreed. Your periodic factory review covers looking back. The slow-tests report (f71-02) now also reads the jobs already recorded: how long developer attempts and Claude jobs took over the last two weeks, how many were cut off, and whether the new 60- and 45-minute limits fit. Anything to change, a limit or a test step, comes as a follow-up ticket or draft ADR for you to approve.
>    Action: F71 D4 rewritten and f71-02 updated. Approving the plan queues f71-01 and f71-02.
>
> Proposals:
> - F71: longer limits, then a report on the slow tests (plan)

## The owner, 2026-10-12 21:33

> I sent back your proposal “F71: longer limits, then a report on the slow tests” (f71-plan).
> - On its key point 5 (Two tickets): the longer attempt needs to happen asap

## The lead, 2026-10-12 21:37

> f71-01 now has priority 0, so it goes to the front of the queue once you approve the plan.
>
> 1. **The longer limits go first in the queue**: f71-01 now has priority 0, the front of the queue, so the runner should take it at its next pick after you approve. Nothing is queued until you approve the plan. The report (f71-02) keeps the card's normal priority and waits its turn.
>    Action: Approve the F71 plan.
> 2. **The one thing faster is doing it yourself**: The change is two numbers in workflow/runner.toml, under [timeouts]: opencode = 3600 and claude = 2700. Limits don't need an ADR, so you can edit them yourself. I haven't checked whether a running runner picks up the new values straight away or only when it restarts. If you do edit them, tell me and I'll drop f71-01 from the plan.
>    Action: Nothing, unless you'd rather edit the two lines yourself.
>
> Proposals:
> - F71: longer limits first, then a report on the slow tests (plan)

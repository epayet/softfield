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

## The lead, 2026-10-13 00:01

> Approved by the owner on 2026-10-13: approved plan/f71: queued f71-02-slow-tests-study

## The lead, 2026-10-21 22:28

> Merged F168 here: The full test suite takes 19 minutes and grows each day:…

## The owner, 2026-10-21 22:28

> From F168, merged here:
> The full test suite takes 19 minutes and grows each day: find the slowest tests (tests/factory_dashboard/test_app.py takes 3 s a test) and make them faster

## The lead, 2026-10-21 22:41

> I've reworked F71 so the tests get faster now, as three tickets at priority 0. The suite has hit its 20-minute limit on 5 of its last 6 runs, so tickets are failing on the test cut alone.
>
> 1. **The slow suite is now stopping tickets**: The full test run averaged 591 s on 10-09, 894 s on 10-16 and 1,193 s today, against a 1,200 s limit. 5 of today's last 6 runs were cut at 1,200 s, whatever the code did. F132's 'Top bar follows the job' ticket (f132-01) and F152's 'Review step on the card' ticket (f152-01) each lost two attempts this way today, and f152-01 is now blocked.
>    Action: Ticket f71-03 first, at priority 0: it gives the test run 40 minutes in the gates and in the developer's shell. This is a stopgap so the line merges again today.
> 2. **Running tests in parallel is the biggest win**: Every run goes one test at a time. Running them side by side should cut the time severalfold on this machine. That's my estimate; f71-04 measures it. The tests and checks stay the same, so no ADR is needed. I'll add pytest-xdist, a common pytest plugin, as a dev dependency myself. It's a new project.toml setting, so other projects run as they do today. Tests that clash when run side by side get fixed, never set to run alone.
>    Action: Ticket f71-04 (lead, priority 0, after f71-03). It also makes check-all print each check's result as it finishes, as decided on 10-13.
> 3. **Making the slowest tests faster**: Each of test_app.py's 81 tests builds its own database and starts a fresh app, which is about 4 minutes in total. My guess is that building the database once and copying it into each test fixes most of that, but the ticket measures first and follows the numbers. No test is removed and no check weakened: the developers need the whole suite. Done when test_app.py takes under a third of today's time. The report also covers the attempt and Claude job times you asked for, plus follow-up tickets for whatever is left.
>    Action: f71-02 reworked from a report into the fix (lead, difficulty 5, priority 0, after f71-04).
> 4. **The developer's 75 minutes stay**: With a 20-minute suite, two check-all runs still fit in an attempt. Raising it a fourth time would only hide the cause, and f71-04 should shorten check-all within a day of approval. If attempts start getting cut at 75 minutes before then, I'll raise it as a one-line follow-up.
>    Action: Nothing.
> 5. **F152's blocked ticket needs bringing back**: f152-01 is blocked only because its tests ran out of time, not because its code failed. Once f71-03 merges, it deserves another run. From F71 I can only change F71's own tickets, so it can't come back from here.
>    Action: Bring f152-01 back in F152's next replan, after f71-03 merges.
> 6. **No need to pause first**: Nothing is running. Until you approve, f71-02 sits at priority 100, behind 64 other tickets, so the line won't reach it. f71-03 and f71-04 only exist on this branch.
>    Action: Approve the replan when you're ready.
>
> Proposals:
> - F71: make the tests faster, starting today (replan)

## The lead, 2026-10-22 07:45

> Done in a terminal session tonight, so this plan isn't applied (its branch is kept as superseded/plan-f71-2026-10-21). The tests now run on 16 workers: check-all takes 4.5 minutes instead of 19.6, and all pass. The time limits stay as they are, so no 40-minute stopgap. f71-02's findings are on the card. Next is f71-03: the browser tests on a fake clock, after f68-07 and f114-08/09/10.

## The lead, 2026-10-22 08:21

> Rejected by the owner on 2026-10-22: won't do

## The lead, 2026-11-05 01:23

> Merged F221 here: Tests are back to being slow again, probably some clock…

## The owner, 2026-11-05 01:23

> From F221, merged here:
> Tests are back to being slow again, probably some clock related tests. Plan to improve test speed, we already run them in parallel they used to take about 4 minutes

## The lead, 2026-11-05 01:26

> The full test run is still about 4 minutes. What grew is the time around it, so this replan puts those gates on workers and moves the clock fix to the front.
>
> 1. **The full run is still about 4 minutes; the slowdown is around it**: The full test run in the gates averaged 218 s on 10-23 and 247 s yesterday, 303 s at most. But each passing developer attempt also runs two other test gates, in one process rather than on the 16 workers: the ticket's own tests, and the check that those tests fail without its code. On one file these take 85–122 s, and up to 414 s for a ticket's own tests and 505 s for the second. All three together took 387 s per passing attempt on 10-22 and 583 s yesterday, with 728 s on 10-28. If you saw a slow number somewhere else, such as a full run well over 5 minutes, tell me where, because the gates don't show it.
>    Action: Ticket f71-04 fixes these two gates.
> 2. **Run those two gates on the workers**: Both gates will use the same 16 workers as the full run. The 'fails without the code' check will also stop at its first failure, because one failure already gives its answer and today it runs every file to the end. The tests and the verdicts stay the same. My estimate is about 4 minutes off each passing attempt, which is not measured yet. On this machine it's a small change.
>    Action: f71-04 (lead, difficulty 2), first.
> 3. **You're partly right about the clock**: Real-time waiting is still in the tests: ten fixed 6-second waits (nine in test_app.py, one in test_overview.py) and about 90 waits with a long time limit, many of them for the pages' 5-second refresh. The ticket for this, f71-03, is written but has never run, because F71 sat at priority 100. The time zone setup added for F187, 'Pages show local time', only sets an environment variable, so I don't expect it's the cause. I can't time individual tests from the planning room, so this is from reading the code. f71-03 measures first and follows what it finds.
>    Action: f71-03 updated: it measures first, covers three more test files (test_thread, test_proposal, test_board) and follows the fake-clock pattern test_line.py already uses. It reports the before and after times. No test is removed or changes what it checks.
> 4. **F71 moves to the front of the board**: I've set F71 to priority 1, ahead of F171, 'Duplicated tickets on the board', which is at 3. It costs two lead tickets of Claude's time up front. Every one of the 100-odd waiting tickets then runs through faster gates, so it pays for itself quickly. If you'd rather keep your board order, say so and I'll put it back.
>    Action: Approving the replan moves it.
> 5. **No new check to stop this coming back**: Developers' branches are already refused when they add a new wait_for_timeout. The risk is lead tickets, which skip that gate, and the suite simply growing. I wouldn't add another gate for that yet. The periodic factory review (F59, Periodic review of the factory) can watch the gate times, which are already recorded.
>    Action: Nothing now; I've noted it on the card for F59.
>
> Proposals:
> - F71: faster test gates, then browser tests on a fake clock (replan)

## The owner, 2026-11-05 23:32

> I sent back your proposal “F71: faster test gates, then browser tests on a fake clock” (f71-replan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-09 16:00

> Checked against main: nothing in the plan is done or taken, so both tickets stand. The only change is that F71 keeps priority 3, the place you gave it on the board.
>
> 1. **Checked against main: nothing is done or taken**: Main hasn't changed the gates, and the slow real-time waits in test_app.py, test_overview.py, test_thread.py and test_planning.py are all still there. test_board.py gained F192's new tests, 'Use the fast lane', with short waits only. The test gates are as slow as before: on 11-06 they averaged 185 s for the ticket's own tests, 250 s for the full run and 151 s for 'fails without the code'. The id f71-04 is still free, and both tickets pass pre-flight.
>    Action: Both tickets stay as drafted. The card notes the check.
> 2. **F71 keeps your board place**: You've since put F71 at priority 3 on the board. That already makes f71-03 eighth in line, so I've dropped my move to priority 1. Inside the card, f71-04 (the faster gates) runs before f71-03 (the fake clock).
>    Action: The card's header stays at 3.
> 3. **Pause before approving**: f71-03 is eighth in the queue on main, and this replan rewrites it to wait for f71-04. If the runner picks the old version first, it builds the narrower ticket without the faster gates in front. Pause the factory from the dashboard, then approve. Approving lifts the pause.
>    Action: Pause, then approve.
>
> Proposals:
> - F71: faster test gates, then browser tests on a fake clock (replan)
